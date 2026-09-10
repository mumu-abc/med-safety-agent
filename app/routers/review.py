"""审查API:支持普通审查、流式 SSE、human-in-the-loop、多轮对话、多Agent协作五种模式。"""
import asyncio
import json
import logging
import queue
import threading
from fastapi import APIRouter, Query
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
    }


@router.post("")
async def review(req: ReviewRequest):
    """提交处方进行安全审查。"""
    # 缓存优先(键含 patient_id 与模式,避免不同患者/不同接口互相污染)
    from app.database import get_db
    cached = get_db().get_cached_review(
        req.prescription_text, patient_id=req.patient_id or "", mode="summary"
    )
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
        "cached": False,
    }
    if memory_context:
        resp["memory_context"] = memory_context

    # 保存到审查缓存
    try:
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

    # 保存到审查缓存
    try:
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
async def review_stream(req: ReviewRequest):
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

        def run_stream():
            try:
                for chunk in graph.stream({"raw_text": prescription_text}, config=config):
                    q.put(("chunk", chunk))
                q.put(("done", None))
            except Exception as e:
                q.put(("error", str(e)))

        thread = threading.Thread(target=run_stream, daemon=True)
        thread.start()

        while True:
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
                # 保存到审查缓存
                try:
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

    # 保存到审查缓存
    try:
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

