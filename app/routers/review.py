"""审查API:支持普通审查、流式 SSE、human-in-the-loop、多轮对话、多Agent协作五种模式。"""
import asyncio
import json
import logging
import queue
import threading
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from app.workflow import (
    review_prescription,
    review_with_hitl,
    resume_review,
    get_review_graph,
)
from app.agents.supervisor_agent import (
    review_multi_agent,
    review_multi_agent_hitl,
    resume_multi_agent,
    get_supervisor_graph,
)
from app.graph.patient_store import get_patient
from app.llm import get_llm
import time
from uuid import uuid4
from app.database import get_db

# ---- 审查历史(替代 ConversationMemory,落盘持久化,重启不丢) ----


def _save_review(thread_id: str, prescription_text: str, result_summary: str = ""):
    """记录一次审查到 DB 历史(重启不丢)。"""
    try:
        get_db().save_review_history(thread_id, prescription_text, result_summary)
    except Exception as e:
        logger.debug(f"审查历史保存跳过: {e}")


def _get_review(thread_id: str) -> dict | None:
    """按 thread_id 查找最近一条审查历史(服务端权威取值)。"""
    try:
        return get_db().get_review_history(thread_id)
    except Exception as e:
        logger.debug(f"审查历史查询跳过: {e}")
        return None


def _list_reviews(n: int = 10) -> list[dict]:
    """获取最近 n 条审查历史。"""
    try:
        return get_db().list_review_history(n)
    except Exception as e:
        logger.debug(f"审查历史列表跳过: {e}")
        return []


def parse_modification(original_text: str, instruction: str) -> str:
    """用 LLM 解析修改指令, 返回新的处方文本。"""
    llm = get_llm()
    prompt = f"""你是一个处方修改助手。根据用户的修改指令, 生成新的处方文本。

原始处方:
{original_text}

用户修改指令:
{instruction}

规则:
1. 只修改指令中提到的药物, 其他药物保持不变
2. 如果是换药, 用新药替换旧药, 剂量用新药的常规剂量
3. 如果是加药, 在原处方后追加新药
4. 如果是去药, 删除指定药物
5. 保持处方格式一致
6. 只输出修改后的处方文本, 不要解释

修改后的处方:"""

    try:
        response = llm.invoke(prompt)
        new_text = response.content.strip()
        if not new_text:
            logger.warning("LLM 返回空处方, 使用原始处方")
            return original_text
        logger.info(f"处方修改: '{instruction}' → {new_text[:100]}...")
        return new_text
    except Exception as e:
        logger.error(f"处方修改解析失败: {e}")
        return original_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/review", tags=["审查"])


class ReviewRequest(BaseModel):
    prescription_text: str
    patient_id: str | None = None


class ResumeRequest(BaseModel):
    thread_id: str


class FeedbackRequest(BaseModel):
    prescription_text: str
    rating: int = Field(ge=1, le=5, description="评分 1-5")
    comment: str = ""
    risk_level: str = "unknown"


class FollowupRequest(BaseModel):
    thread_id: str
    original_text: str = ""  # 兜底:thread_id 查不到时用客户端传入的处方
    instruction: str  # 例: "把布洛芬换成对乙酰氨基酚"


def _enrich_with_patient(text: str, patient_id: str | None) -> str:
    """将患者档案信息追到处方文本中。"""
    if not patient_id:
        return text
    patient = get_patient(patient_id)
    if not patient:
        return text
    extra = []
    if patient.get("age"):
        extra.append(f"年龄:{patient['age']}岁")
    if patient.get("gender"):
        extra.append(f"性别:{patient['gender']}")
    if patient.get("conditions"):
        extra.append(f"疾病:{','.join(patient['conditions'])}")
    if patient.get("allergies"):
        extra.append(f"过敏史:{','.join(patient['allergies'])}")
    if patient.get("liver_function") and patient["liver_function"] != "normal":
        extra.append(f"肝功能:{patient['liver_function']}")
    if patient.get("renal_function") and patient["renal_function"] != "normal":
        extra.append(f"肾功能:{patient['renal_function']}")
    if patient.get("pregnancy") == "yes":
        extra.append("孕期:是")
    if extra:
        text += f"\n患者信息:{'; '.join(extra)}"
    return text


def _get(result, key, default=None):
    """兼容 dict 和 AttrDict/对象取值。"""
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)


def _memory_enabled() -> bool:
    """记忆系统是否开启。

    记忆依赖 sentence-transformers + faiss,首次调用要下载约 400MB 的 bge-small-zh 模型,
    常驻后占用数百 MB 内存。公网免费层(Render 512MB / Railway 500MB)会直接 OOM,
    部署时设 ENABLE_MEMORY=false 即可关闭;核心审查链路(图谱 + 规则 + LLM)不受影响。
    """
    from app.config import settings
    return bool(getattr(settings, "enable_memory", True))


def _is_review_cacheable(result_or_resp) -> bool:
    """判断一次审查结果是否值得写入缓存。

    不缓存「一个药都没识别出来」或「风险未知」的结果。这类结果通常意味着
    解析失败或依赖异常(LLM 超时、图谱未加载等);如果把它缓存 7 天,
    错误的"安全"结论会在 TTL 内被反复命中——这是安全关键系统最糟的失败模式:
    一次瞬时故障,变成长期错误的临床判断。

    入参可以是工作流状态(对象/AttrDict),也可以是已构建好的响应 dict。
    """
    if isinstance(result_or_resp, dict):
        rx = result_or_resp.get("prescription") or {}
        drugs = rx.get("drugs") or [] if isinstance(rx, dict) else (getattr(rx, "drugs", None) or [])
        if not drugs:
            return False
        return result_or_resp.get("risk_level") != "unknown"

    rx = _get(result_or_resp, "prescription")
    drugs = (getattr(rx, "drugs", None) or []) if rx is not None else []
    if not drugs:
        return False
    risk = _get(result_or_resp, "risk_assessment")
    if risk is not None and getattr(risk, "overall_risk", None) == "unknown":
        return False
    return True


def _brief(text, n: int = 90) -> str:
    """压成一行短句,用于推理链的 detail。"""
    s = " ".join(str(text or "").split())
    return s[:n] + ("…" if len(s) > n else "")


# 缓存条目必须带上的字段 —— 结构升级后,老缓存不能原样返回给前端。
# 2026-09-19 踩坑:reasoning_chain 是新加的字段,存量和线上老缓存里都没有;
# 而缓存命中时是**原样返回**的,于是前端"推理链"tab 依旧空白,
# 看起来像"代码改了却没生效"。所以结构过期的缓存一律当作 miss 重新计算。
_CACHE_REQUIRED_FIELDS = ("reasoning_chain",)
# risk_assessment 内部新增的系统字段：老缓存的 risk_assessment 里没有它，
# 命中就会静默丢掉「地板抬升」提示 —— 与 reasoning_chain 是同一类坑，一并作废重算。
_CACHE_REQUIRED_RISK_FIELDS = ("floor_applied",)


def _is_cache_schema_current(payload) -> bool:
    """缓存条目的结构是否还是当前版本;缺字段/空值即作废重算。"""
    if not isinstance(payload, dict):
        return False
    for field in _CACHE_REQUIRED_FIELDS:
        value = payload.get(field)
        if field == "reasoning_chain":
            # 空列表同样视为过期:前端拿到空数组还是显示空面板
            if not isinstance(value, list) or not value:
                return False
        elif value is None:
            return False
    ra = payload.get("risk_assessment")
    if isinstance(ra, dict):
        for field in _CACHE_REQUIRED_RISK_FIELDS:
            if field not in ra:
                return False
    return True


def _build_reasoning_chain(result) -> list[dict]:
    """把流水线各节点的**实际输出**整理成一条可追溯的推理链。

    设计要点:
      · 纯派生 —— 不额外调用 LLM。成本 0,也不会和报告内容打架。
      · 每一步都带真实计数/等级,不是"正在分析中…"这类套话。
      · 与 LangGraph 的节点一一对应(parse/detect/rules/assess/recommend/gen_report),
        前端点开任意一步都能对到 trace 里的同名节点。
    """
    rx = _get(result, "prescription")
    risk = _get(result, "risk_assessment")
    alt = _get(result, "alternatives")

    patient = _get(result, "patient") or {}
    drug_names = _get(result, "drug_names") or []
    interactions = _get(result, "interactions") or []
    contraindications = _get(result, "contraindications") or []
    rule_risks = _get(result, "rule_risks") or []
    report = _get(result, "report", "") or ""

    chain: list[dict] = []

    # 1. 处方解析
    if not drug_names and rx is not None:
        drug_names = [getattr(d, "name", "") for d in (_get(rx, "drugs") or [])]
    drug_names = [n for n in drug_names if n]
    if drug_names:
        detail = f"从处方文本中识别出 {len(drug_names)} 种药物:{'、'.join(drug_names)}"
    else:
        detail = "未从处方文本中识别出药物(解析失败或文本不含药名)"
    if patient.get("age"):
        detail += f";患者 {patient['age']} 岁"
    if patient.get("conditions"):
        detail += f",基础疾病:{'、'.join(patient['conditions'])}"
    chain.append({"step": "① 处方解析", "detail": detail, "node": "parse"})

    # 2. 知识图谱检索
    if interactions:
        top = interactions[0]
        a = _get(top, "drug_a", "?")
        b = _get(top, "drug_b", "?")
        sev = _get(top, "severity", "")
        detail = f"图谱命中 {len(interactions)} 条相互作用,其中最高危为 {a} + {b}({sev})"
        mech = _get(top, "mechanism", "")
        if mech:
            detail += f" —— {_brief(mech, 60)}"
    elif len(drug_names) == 1:
        detail = f"处方仅含 1 种药物({drug_names[0]}),不存在药物-药物相互作用"
    else:
        detail = "图谱未命中相互作用(药名可能未归一,或确实无已知交互)"
    chain.append({"step": "② 知识图谱检索", "detail": detail, "node": "detect"})

    # 3. 规则引擎
    detail = f"触发 {len(rule_risks)} 条安全规则、{len(contraindications)} 条禁忌判定"
    if contraindications:
        c0 = contraindications[0]
        detail += f";首条禁忌:{_get(c0, 'drug', '?')} × {_get(c0, 'condition', '?')}"
    chain.append({"step": "③ 规则引擎", "detail": detail, "node": "rules"})

    # 4. 语义风险评估
    level = _get(risk, "overall_risk", "unknown") if risk else "unknown"
    detail = f"LLM 综合图谱与规则结果,判定整体风险等级为 {level}"
    summary = _get(risk, "summary", "") if risk else ""
    if summary:
        detail += f"。{_brief(summary, 100)}"
    # 地板生效时,上面那句"LLM 判定为 X"其实不成立 —— 这里必须把真相写出来,
    # 否则推理链本身就成了误导来源。
    if risk and _get(risk, "floor_applied", False):
        orig = _get(risk, "llm_original_risk", "") or "unknown"
        if orig == "unknown":
            detail += "。⚠️ 注:LLM 未给出有效等级,该等级由规则/图谱判定,并非 LLM 判断"
        else:
            detail += f"。⚠️ 注:LLM 原判为 {orig},该等级由安全规则/图谱地板抬升而来,并非 LLM 判断"
    chain.append({"step": "④ 语义风险评估", "detail": detail, "node": "assess"})

    # 5. 替代方案(条件分支:仅在触发高风险时执行)
    sugs = (_get(alt, "suggestions", []) or []) if alt else []
    if sugs:
        names = "、".join(str(_get(s, "original_drug", "?")) for s in sugs)
        detail = f"高风险触发替代方案分支,为 {len(sugs)} 种药物给出替换建议:{names}"
        asum = _get(alt, "summary", "")
        if asum:
            detail += f"。{_brief(asum, 80)}"
    else:
        detail = "未触发替代方案分支(整体风险未达阈值,无需换药)"
    chain.append({"step": "⑤ 替代方案推荐", "detail": detail, "node": "recommend"})

    # 6. 报告聚合
    chain.append({
        "step": "⑥ 报告聚合",
        "detail": f"汇总以上各步结论,生成 {len(report)} 字的审查报告",
        "node": "gen_report",
    })

    return chain


def _build_raw_response(result) -> dict:
    """从审查结果构建结构化响应(复用于 /raw、/stream、/hitl)。"""
    rx = _get(result, "prescription")
    risk = _get(result, "risk_assessment")
    alt = _get(result, "alternatives")

    # 安全提取 drugs 和 patient
    drugs_list = []
    patient_info = {}
    if rx:
        try:
            drugs_list = [
                {"name": d.name, "dosage": d.dosage, "frequency": d.frequency}
                for d in (rx.drugs or [])
            ]
        except Exception:
            pass
        try:
            p = rx.patient
            if p:
                patient_info = {
                    "age": p.age, "gender": p.gender,
                    "conditions": p.conditions, "allergies": p.allergies,
                }
        except Exception:
            pass

    return {
        "report": _get(result, "report", ""),
        "interactions": _get(result, "interactions", []),
        "contraindications": _get(result, "contraindications", []),
        "rule_risks": _get(result, "rule_risks", []),
        "risk_assessment": {
            "overall_risk": risk.overall_risk if risk else "unknown",
            "risks": [
                {"drug": r.drug, "risk_type": r.risk_type, "severity": r.severity,
                 "description": r.description, "source": r.source, "suggestion": r.suggestion}
                for r in (risk.risks if risk else [])
            ],
            "summary": risk.summary if risk else "",
            # 可解释性：让前端/报告能区分「LLM 自己判的等级」和「规则强制抬升的等级」
            # （risk 可能是 dict 也可能是对象，统一走 _get）
            "floor_applied": bool(_get(risk, "floor_applied", False)),
            "llm_original_risk": _get(risk, "llm_original_risk", "") or "",
        } if risk else None,
        "alternatives": {
            "suggestions": [
                {"original": s.original_drug,
                 "alternatives": [
                     {"name": a.name, "category": a.category, "reason": a.reason}
                     for a in (s.alternatives or [])
                 ],
                 "reason": s.reason}
                for s in (alt.suggestions if alt else [])
            ],
            "summary": alt.summary if alt else "",
        } if alt else None,
        "prescription": {
            "diagnosis": rx.diagnosis if rx else "",
            "drugs": drugs_list,
            "patient": patient_info,
        },
        "reasoning_chain": _build_reasoning_chain(result),
    }


@router.post("")
async def review(req: ReviewRequest):
    """提交处方进行安全审查。"""
    # 缓存优先(键含 patient_id 与模式,避免不同患者/不同接口互相污染)
    from app.database import get_db
    cached = get_db().get_cached_review(
        req.prescription_text, patient_id=req.patient_id or "", mode="summary"
    )
    if cached and not _is_cache_schema_current(cached):
        logger.info("♻️ 缓存结构过期(字段不全),忽略该缓存重新审查")
        cached = None
    if cached:
        logger.info("⚡ 缓存命中，直接返回历史结果")
        cached["cached"] = True
        return cached

    try:
        loop = asyncio.get_running_loop()
        # 记忆检索：查找相似历史案例
        # retrieve_memories 首次调用会加载 SentenceTransformer(联网下载 + CPU 编码),
        # 同步执行会阻塞整个事件循环,必须放进 executor
        memory_context = ""
        try:
            if not _memory_enabled():
                raise ImportError("记忆系统已通过 ENABLE_MEMORY=false 关闭")
            from app.memory import retrieve_memories, format_memories_for_context
            memories = await loop.run_in_executor(
                None, lambda: retrieve_memories(req.prescription_text, top_k=3)
            )
            if memories:
                memory_context = format_memories_for_context(memories)
                logger.info(f"🧠 检索到 {len(memories)} 条相关记忆")
        except Exception as e:
            logger.debug(f"记忆检索跳过: {e}")

        prescription_text = _enrich_with_patient(req.prescription_text, req.patient_id)
        result = await loop.run_in_executor(None, review_prescription, prescription_text)
    except Exception as e:
        logger.exception("审查流程异常")
        return JSONResponse(
            status_code=500,
            content={"error": f"审查流程异常: {type(e).__name__}: {str(e)}"},
        )
    # 记录审查历史(用于多轮对话)
    risk_assessment = _get(result, "risk_assessment")
    summary = risk_assessment.summary if risk_assessment else ""
    thread_id = f"conv-{uuid4().hex}"
    _save_review(thread_id, req.prescription_text, summary)

    # 保存审查案例到记忆
    try:
        if not _memory_enabled():
            raise ImportError("记忆系统已通过 ENABLE_MEMORY=false 关闭")
        from app.memory import extract_and_save_case
        risk_level = risk_assessment.overall_risk if risk_assessment else "unknown"
        rx_for_mem = _get(result, "prescription")
        drug_names = [d.name for d in (rx_for_mem.drugs or [])] if rx_for_mem else []
        await loop.run_in_executor(
            None,
            lambda: extract_and_save_case(req.prescription_text, risk_level, summary, drug_names),
        )
    except Exception as e:
        logger.debug(f"记忆保存跳过: {e}")

    # 安全提取处方信息(prescription 可能为 None)
    rx = _get(result, "prescription")
    drugs_list = []
    patient_info = {}
    if rx:
        try:
            drugs_list = [
                {"name": d.name, "dosage": d.dosage, "frequency": d.frequency}
                for d in (rx.drugs or [])
            ]
            patient_info = {
                "age": rx.patient.age if rx.patient else "",
                "gender": rx.patient.gender if rx.patient else "",
                "conditions": rx.patient.conditions if rx.patient else [],
                "allergies": rx.patient.allergies if rx.patient else [],
            }
        except Exception:
            pass

    resp = {
        "thread_id": thread_id,
        "report": _get(result, "report", ""),
        "prescription": {
            "diagnosis": rx.diagnosis if rx else "",
            "drugs": drugs_list,
            "patient": patient_info,
        },
        "risk_level": risk_assessment.overall_risk if risk_assessment else "unknown",
        "interactions_count": len(_get(result, "interactions", [])),
        "rule_risks_count": len(_get(result, "rule_risks", [])),
        "has_alternatives": bool(_get(result, "alternatives")),
        "reasoning_chain": _build_reasoning_chain(result),
        "cached": False,
    }
    if memory_context:
        resp["memory_context"] = memory_context

    # 保存到审查缓存(解析失败/风险未知的结果不缓存,避免错误结论在 TTL 内反复命中)
    try:
        if _is_review_cacheable(result):
            get_db().save_review_cache(
                req.prescription_text, resp, patient_id=req.patient_id or "", mode="summary"
            )
    except Exception as e:
        logger.debug(f"缓存保存跳过: {e}")

    return resp


@router.post("/raw")
async def review_raw(req: ReviewRequest):
    """返回完整结构化数据。"""
    # 缓存优先
    from app.database import get_db
    cached = get_db().get_cached_review(
        req.prescription_text, patient_id=req.patient_id or "", mode="raw"
    )
    if cached and not _is_cache_schema_current(cached):
        logger.info("♻️ 缓存结构过期(字段不全),忽略该缓存重新审查")
        cached = None
    if cached:
        cached["cached"] = True
        return cached

    try:
        prescription_text = _enrich_with_patient(req.prescription_text, req.patient_id)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, review_prescription, prescription_text)
    except Exception as e:
        logger.exception("审查流程异常")
        return JSONResponse(
            status_code=500,
            content={"error": f"审查流程异常: {type(e).__name__}: {str(e)}"},
        )
    # 记录审查历史
    summary = result.risk_assessment.summary if result.risk_assessment else ""
    thread_id = f"conv-{uuid4().hex}"
    _save_review(thread_id, req.prescription_text, summary)
    resp = _build_raw_response(result)
    resp["thread_id"] = thread_id
    resp["cached"] = False

    # 保存到审查缓存(同上:不缓存解析失败的结果)
    try:
        if _is_review_cacheable(result):
            get_db().save_review_cache(
                req.prescription_text, resp, patient_id=req.patient_id or "", mode="raw"
            )
    except Exception as e:
        logger.debug(f"缓存保存跳过: {e}")

    return resp


@router.post("/followup")
async def review_followup(req: FollowupRequest):
    """多轮对话: 基于上次审查结果, 根据修改指令重新审查。

    示例:
    - 第一次: POST /api/review {prescription_text: "华法林5mg, 布洛芬200mg"}
    - 返回: {thread_id: "conv-xxx", ...}
    - 追问: POST /api/review/followup {thread_id: "conv-xxx", instruction: "把布洛芬换成对乙酰氨基酚"}
    - 返回: 重新审查的完整结果
    """
    try:
        prior = _get_review(req.thread_id)
        original_text = (prior or {}).get("prescription_text") or req.original_text

        # 1. 用 LLM 解析修改指令, 生成新处方
        loop = asyncio.get_running_loop()
        new_text = await loop.run_in_executor(
            None, parse_modification, original_text, req.instruction
        )

        # 2. 重新审查
        result = await loop.run_in_executor(None, review_prescription, new_text)

        # 3. 记录审查历史
        ra = _get(result, "risk_assessment")
        summary = ra.summary if ra else ""
        new_thread_id = f"conv-followup-{uuid4().hex}"
        _save_review(new_thread_id, new_text, summary)

    except Exception as e:
        logger.exception("多轮对话审查异常")
        return JSONResponse(
            status_code=500,
            content={"error": f"多轮对话异常: {type(e).__name__}: {str(e)}"},
        )
    rx = _get(result, "prescription")
    drugs_list = []
    if rx:
        try:
            drugs_list = [
                {"name": d.name, "dosage": d.dosage, "frequency": d.frequency}
                for d in (rx.drugs or [])
            ]
        except Exception:
            pass

    ra = _get(result, "risk_assessment")
    return {
        "thread_id": new_thread_id,
        "original_text": original_text,
        "modified_text": new_text,
        "instruction": req.instruction,
        "report": _get(result, "report", ""),
        "prescription": {
            "diagnosis": rx.diagnosis if rx else "",
            "drugs": drugs_list,
        },
        "risk_level": ra.overall_risk if ra else "unknown",
        "interactions_count": len(_get(result, "interactions", [])),
        "rule_risks_count": len(_get(result, "rule_risks", [])),
        "has_alternatives": bool(_get(result, "alternatives")),
    }


@router.post("/stream")
async def review_stream(req: ReviewRequest, request: Request):
    """流式审查:用 SSE 返回每个步骤进度 + 最终结构化结果。

    前端用 fetch + ReadableStream 消费:
    - {node: "parse", label: "📋 解析处方"}  — 每步完成事件
    - {status: "complete", result: {...}}     — 最终完整结果
    - {error: "..."}                          — 错误
    """
    # 先查缓存(使用原始处方文本,不包含患者信息)
    from app.database import get_db
    cached = get_db().get_cached_review(
        req.prescription_text, patient_id=req.patient_id or "", mode="raw"
    )
    if cached and not _is_cache_schema_current(cached):
        logger.info("♻️ 缓存结构过期(字段不全),忽略该缓存重新审查")
        cached = None
    if cached:
        async def cached_generator():
            cached["cached"] = True
            yield f"data: {json.dumps({'status': 'complete', 'result': cached, 'cached': True}, ensure_ascii=False, default=str)}\n\n"
        return StreamingResponse(cached_generator(), media_type="text/event-stream")

    prescription_text = _enrich_with_patient(req.prescription_text, req.patient_id)

    async def event_generator():
        loop = asyncio.get_running_loop()
        graph = get_review_graph()
        thread_id = f"stream-{uuid4().hex}"
        config = {"configurable": {"thread_id": thread_id}}

        node_labels = {
            "parse": "📋 解析处方",
            "detect": "🔍 检测药物交互",
            "rules": "📐 规则引擎检查",
            "assess": "⚠️ 评估风险等级",
            "recommend": "💊 推荐替代方案",
            "gen_report": "📝 生成审查报告",
        }

        q: queue.Queue = queue.Queue()

        # 自动完成模式无 checkpointer,直接从流式输出累积最终状态
        state_values: dict = {"raw_text": prescription_text}

        # 客户端断开(关页面/取消请求)时置位,让后台线程尽快停下,
        # 否则它会继续跑完整个图并持续调用 LLM,白白烧 token。
        stop = threading.Event()

        def run_stream():
            try:
                for chunk in graph.stream({"raw_text": prescription_text}, config=config):
                    if stop.is_set():
                        return
                    q.put(("chunk", chunk))
                q.put(("done", None))
            except Exception as e:
                q.put(("error", str(e)))

        thread = threading.Thread(target=run_stream, daemon=True)
        thread.start()

        while True:
            if await request.is_disconnected():
                stop.set()
                logger.info("客户端断开连接,已中止流式审查")
                break

            try:
                kind, data = await loop.run_in_executor(None, q.get, 300.0)
            except Exception:
                yield f"data: {json.dumps({'error': '处理超时'}, ensure_ascii=False)}\n\n"
                break

            if kind == "done":
                try:
                    response_data = _build_raw_response(state_values)
                except Exception as e:
                    logger.warning(f"从流式状态构建响应失败,回退到直接审查: {e}")
                    try:
                        fallback = await loop.run_in_executor(None, review_prescription, prescription_text)
                        response_data = _build_raw_response(fallback)
                    except Exception as e2:
                        yield f"data: {json.dumps({'error': f'构建响应失败: {e2}'}, ensure_ascii=False)}\n\n"
                        break
                response_data["cached"] = False
                # 保存到审查缓存(不缓存解析失败的结果)
                try:
                    if _is_review_cacheable(response_data):
                        get_db().save_review_cache(
                            req.prescription_text, response_data,
                            patient_id=req.patient_id or "", mode="raw",
                        )
                except Exception as e:
                    logger.debug(f"缓存保存跳过: {e}")
                yield f"data: {json.dumps({'status': 'complete', 'result': response_data}, ensure_ascii=False, default=str)}\n\n"
                break
            elif kind == "error":
                yield f"data: {json.dumps({'error': data}, ensure_ascii=False)}\n\n"
                break
            elif kind == "chunk":
                for node_name, values in data.items():
                    if isinstance(values, dict):
                        state_values.update(values)
                    yield f"data: {json.dumps({'node': node_name, 'label': node_labels.get(node_name, node_name)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/cache/stats")
async def cache_stats():
    """查看审查缓存统计。"""
    from app.database import get_db
    return get_db().get_cache_stats()


@router.delete("/cache")
async def clear_cache():
    """清空审查缓存。"""
    from app.database import get_db
    count = get_db().clear_expired_cache(days=0)
    return {"cleared": count}


@router.post("/hitl")
async def review_hitl(req: ReviewRequest):
    """human-in-the-loop 审查:在替代方案推荐前暂停,等待药师确认。

    流程:
    1. 跑 parse → detect → rules → assess,在 alternatives 前中断
    2. 返回风险评估结果 + thread_id
    3. 药师确认后调 POST /api/review/hitl/resume 继续
    """
    try:
        prescription_text = _enrich_with_patient(req.prescription_text, req.patient_id)
        loop = asyncio.get_running_loop()
        result, thread_id, needs_resume = await loop.run_in_executor(
            None, review_with_hitl, prescription_text
        )
    except Exception as e:
        logger.exception("HITL 审查流程异常")
        return JSONResponse(
            status_code=500,
            content={"error": f"审查流程异常: {type(e).__name__}: {str(e)}"},
        )
    return {
        "thread_id": thread_id,
        "needs_resume": needs_resume,
        "partial_result": _build_raw_response(result),
    }


@router.post("/hitl/resume")
async def review_hitl_resume(req: ResumeRequest):
    """恢复被中断的审查流程:从 alternatives 继续到 report。"""
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, resume_review, req.thread_id)
    except Exception as e:
        logger.exception("恢复审查流程异常")
        return JSONResponse(
            status_code=500,
            content={"error": f"恢复异常: {type(e).__name__}: {str(e)}"},
        )
    return _build_raw_response(result)


@router.get("/conversations")
async def list_conversations():
    """查询对话历史(最近 10 轮)。"""
    turns = _list_reviews(10)
    return {
        "conversations": [
            {
                "thread_id": t["thread_id"],
                "prescription_text": t["prescription_text"][:100],
                "result_summary": t["result_summary"],
                "timestamp": t["timestamp"],
            }
            for t in turns
        ]
    }


# ---- 多 Agent 协作模式 ----

@router.post("/multi")
async def review_multi(req: ReviewRequest):
    """多 Agent 协作审查。

    与普通审查的区别:
    1. Supervisor 编排:detect 和 rules 并行执行(fan-out)
    2. 风险评估后动态触发替代方案 Agent
    3. agent_history 返回执行路径,可用于追踪和调试
    """
    # 缓存优先
    from app.database import get_db
    cached = get_db().get_cached_review(
        req.prescription_text, patient_id=req.patient_id or "", mode="multi"
    )
    if cached and not _is_cache_schema_current(cached):
        logger.info("♻️ 缓存结构过期(字段不全),忽略该缓存重新审查")
        cached = None
    if cached:
        cached["cached"] = True
        return cached

    try:
        prescription_text = _enrich_with_patient(req.prescription_text, req.patient_id)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, review_multi_agent, prescription_text)
    except Exception as e:
        logger.exception("多Agent审查异常")
        return JSONResponse(
            status_code=500,
            content={"error": f"多Agent审查异常: {type(e).__name__}: {str(e)}"},
        )
    resp = _build_raw_response(result)
    resp["cached"] = False

    # 保存到审查缓存(同上:不缓存解析失败的结果)
    try:
        if _is_review_cacheable(resp):
            get_db().save_review_cache(
                req.prescription_text, resp, patient_id=req.patient_id or "", mode="multi"
            )
    except Exception as e:
        logger.debug(f"缓存保存跳过: {e}")

    return resp


@router.post("/multi/hitl")
async def review_multi_hitl(req: ReviewRequest):
    """多 Agent + human-in-the-loop 审查。

    在替代方案推荐前暂停,等待药师确认。
    """
    try:
        prescription_text = _enrich_with_patient(req.prescription_text, req.patient_id)
        loop = asyncio.get_running_loop()
        result, thread_id, needs_resume = await loop.run_in_executor(
            None, review_multi_agent_hitl, prescription_text
        )
    except Exception as e:
        logger.exception("多Agent HITL审查异常")
        return JSONResponse(
            status_code=500,
            content={"error": f"审查异常: {type(e).__name__}: {str(e)}"},
        )
    return {
        "thread_id": thread_id,
        "needs_resume": needs_resume,
        "partial_result": _build_raw_response(result),
        "agent_history": result.get("agent_history", []),
    }


@router.post("/multi/resume")
async def review_multi_resume(req: ResumeRequest):
    """恢复被中断的多 Agent 审查。"""
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, resume_multi_agent, req.thread_id)
    except Exception as e:
        logger.exception("恢复多Agent审查异常")
        return JSONResponse(
            status_code=500,
            content={"error": f"恢复异常: {type(e).__name__}: {str(e)}"},
        )
    return _build_raw_response(result)


# ── 反馈 API ──────────────────────────────────────────────

@router.post("/feedback")
async def submit_review_feedback(req: FeedbackRequest):
    """提交审查反馈，同时存入记忆系统。"""
    try:
        from app.database import db
        fb_id = db.save_feedback(req.prescription_text[:100], req.rating, req.comment)

        # 存入向量记忆
        try:
            if not _memory_enabled():
                raise ImportError("记忆系统已通过 ENABLE_MEMORY=false 关闭")
            from app.memory import extract_memories_from_feedback
            extract_memories_from_feedback(req.prescription_text, req.rating, req.comment, req.risk_level)
        except Exception as e:
            logger.debug(f"反馈记忆保存跳过: {e}")

        return {"status": "ok", "feedback_id": fb_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/feedback/stats")
async def get_feedback_stats():
    """获取反馈统计。"""
    try:
        from app.database import db
        feedback = db.get_recent_feedback(limit=50)
        if not feedback:
            return {"status": "ok", "count": 0, "avg_rating": 0, "feedback": []}
        avg = sum(f["rating"] for f in feedback) / len(feedback)
        return {"status": "ok", "count": len(feedback), "avg_rating": round(avg, 1), "feedback": feedback[:10]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

