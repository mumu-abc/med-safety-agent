"""处方解析Agent:用 LLM + JSON 手动解析从自由文本提取结构化处方。

设计要点:
1. with_structured_output 强约束输出格式,不会返回乱七八糟的文本。
2. Pydantic schema 就是"合同"——LLM必须按这个格式输出。
3. 同时提取患者信息(年龄/性别/肝肾功能/过敏史),为后续风险评估提供输入。
"""
import json
import logging
import re
from typing import Any
from pydantic import BaseModel, Field, model_validator
from langchain_core.messages import HumanMessage, SystemMessage
from app.llm import get_llm

logger = logging.getLogger(__name__)

# LLM 常用来表示"没这个信息"的占位符
_BLANK_TOKENS = {"", "null", "none", "unknown", "未知", "不详", "未提供", "无", "-", "--", "n/a", "na"}


def _blank_to_none(v: Any) -> Any:
    """把空串/占位符归一为 None。

    踩过的坑:早期用 `re.sub(r':\\s*null', ': ""', ...)` 把所有 null 统一替换成空串,
    结果 `"age": ""` 过不了 `int | None` 校验,**整个处方解析抛异常退回空处方**,
    系统对一张真实处方输出"药物列表为空 → 安全"。这是安全关键系统最危险的假阴性。
    """
    if isinstance(v, str) and v.strip().lower() in _BLANK_TOKENS:
        return None
    return v


class DrugItem(BaseModel):
    """处方中的一个药品。"""
    name: str = Field(description="药品名称")
    dosage: str | None = Field(default="", description="剂量,如'5mg'、'100mg'")
    frequency: str | None = Field(default="", description="频次,如'qd'(每日一次)、'bid'(每日两次)")
    duration: str | None = Field(default="", description="疗程,如'7天'、'长期'")


class PatientInfo(BaseModel):
    """患者信息。"""
    age: int | None = Field(default=None, description="年龄")
    gender: str | None = Field(default="", description="性别:男/女")
    conditions: list[str] | None = Field(default_factory=list, description="现有疾病/诊断")
    allergies: list[str] | None = Field(default_factory=list, description="已知过敏史")
    liver_function: str | None = Field(default="normal", description="肝功能: normal/impaired/unknown")
    renal_function: str | None = Field(default="normal", description="肾功能: normal/impaired/unknown")
    pregnancy: str | None = Field(default="no", description="是否怀孕: yes/no/unknown")

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: Any) -> Any:
        """容错归一化:让"信息缺失"的表达方式不影响解析成功。

        LLM 对缺失年龄可能输出 "" / null / "未知" / "68岁" 等各种形式,
        这里统一收敛,避免整张处方因一个字段校验失败而全丢。
        """
        if not isinstance(data, dict):
            return data
        data = dict(data)

        age = data.get("age")
        if isinstance(age, str):
            m = re.search(r"\d+", age)
            data["age"] = int(m.group()) if m else None
        elif isinstance(age, float):
            data["age"] = int(age)
        else:
            data["age"] = _blank_to_none(age)

        for key in ("gender", "liver_function", "renal_function", "pregnancy"):
            v = _blank_to_none(data.get(key))
            if v is None:
                data.pop(key, None)  # 缺失就用字段默认值
            else:
                data[key] = v

        for key in ("conditions", "allergies"):
            v = data.get(key)
            if v is None or (isinstance(v, str) and not v.strip()):
                data[key] = []
            elif isinstance(v, str):
                data[key] = [v]

        return data


class Prescription(BaseModel):
    """结构化处方。"""
    drugs: list[DrugItem] = Field(default_factory=list, description="处方药品列表")
    patient: PatientInfo = Field(default_factory=PatientInfo, description="患者信息")
    diagnosis: str = Field(default="", description="临床诊断")


PARSE_SYSTEM = """你是一个专业药剂师。从以下处方文本中提取结构化信息。

规则:
1. 识别所有药品名称、剂量、频次、疗程
2. 提取患者信息(年龄、性别、疾病、过敏史、肝肾功能)
3. 如果信息缺失,留空即可,不要编造
4. 药品名称用通用名(如"阿司匹林"而非"aspirin")

你必须只输出一个JSON对象,不要输出任何其他文字。JSON格式如下:
{
  "drugs": [{"name": "药品名", "dosage": "剂量", "frequency": "频次", "duration": "疗程"}],
  "patient": {"age": null, "gender": "", "conditions": [], "allergies": [], "liver_function": "normal", "renal_function": "normal", "pregnancy": "no"},
  "diagnosis": "诊断"
}"""


def _fallback_parse(text: str) -> Prescription:
    """LLM 解析失败时的确定性兜底:用图谱已知药名对原文做字面匹配。

    为什么必须有兜底:空处方会被下游当作"没有药物 → 没有风险 → 安全",
    而真实原因是解析失败。安全关键系统里,「解析失败」必须被看见,
    至少要用规则把能认出的药认出来。
    """
    try:
        from app.graph.drug_graph import get_all_drugs
        # 长名字优先,避免"阿司匹林"先命中导致"阿司匹林肠溶片"漏掉
        names = sorted(
            {d.get("name", "") for d in get_all_drugs() if d.get("name")},
            key=len, reverse=True,
        )
    except Exception as e:  # 图谱坏了也要能返回,不能让兜底再抛异常
        logger.error(f"兜底解析无法加载药名: {e}")
        return Prescription(diagnosis="", drugs=[], patient=PatientInfo())

    found: list[DrugItem] = []
    consumed: list[tuple[int, int]] = []
    for name in names:
        start = 0
        while True:
            idx = text.find(name, start)
            if idx < 0:
                break
            end = idx + len(name)
            if not any(s <= idx < e for s, e in consumed):
                consumed.append((idx, end))
                found.append(DrugItem(name=name))
            start = end
    found.sort(key=lambda d: text.find(d.name))
    logger.warning("LLM 解析失败,启用字面兜底,识别到 %d 种药物: %s",
                   len(found), [d.name for d in found])
    return Prescription(diagnosis="", drugs=found, patient=PatientInfo())


def parse_prescription(text: str) -> Prescription:
    """从自由文本解析结构化处方。手动解析JSON输出。带重试 + 确定性兜底。"""
    if not (text or "").strip():
        return Prescription(diagnosis="", drugs=[], patient=PatientInfo())

    last_err: Exception | None = None
    for attempt in range(3):
        try:
            parsed = _parse_once(text)
            # 解析成功但一个药都没认出来,同样视为失败,交给兜底
            if parsed.drugs:
                return parsed
            last_err = ValueError("LLM 返回了 0 种药物")
            logger.warning(f"处方解析第{attempt+1}次返回空药物列表")
        except Exception as e:
            last_err = e
            logger.warning(f"处方解析第{attempt+1}次失败: {e}")
        import time
        time.sleep(1.5 * (attempt + 1))

    logger.error(f"处方解析最终失败,转确定性兜底: {last_err}")
    return _fallback_parse(text)


def _parse_once(text: str) -> Prescription:
    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=PARSE_SYSTEM),
        HumanMessage(content=f"处方文本:\n{text}"),
    ])
    content = response.content
    logger.info(f"LLM 原始返回: {repr(content[:500])}")
    content = content.strip() if content else ""
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    if content.startswith("json"):
        content = content[4:]
    content = content.strip()

    # 注意:这里**不能**把 null 统一替换成 ""。
    # 早期实现用 re.sub(r':\s*null', ': ""') 做这件事,结果 patient.age 变成 "",
    # 过不了 int | None 校验,整张处方被丢掉 → 系统报"安全"。
    # JSON 原生 null 对 Optional 字段是合法值,交给 Pydantic 处理即可。
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # 模型偶尔在 JSON 前后夹带说明文字,退一步截出第一个 {...} 再试
        m = re.search(r"\{.*\}", content, re.S)
        if not m:
            raise
        data = json.loads(m.group())

    if not isinstance(data, dict):
        raise ValueError(f"LLM 返回的不是 JSON 对象: {type(data).__name__}")

    drugs = data.get("drugs") or []
    if isinstance(drugs, dict):
        drugs = [drugs]
    normalized: list[dict] = []
    for drug in drugs:
        if isinstance(drug, str):  # 模型有时只给药名字符串
            drug = {"name": drug}
        if not isinstance(drug, dict):
            continue
        drug.setdefault("name", "")
        if not str(drug.get("name", "")).strip():
            continue  # 丢弃没名字的条目,避免下游拿到空药名
        drug.setdefault("dosage", "")
        drug.setdefault("frequency", "")
        drug.setdefault("duration", "")
        normalized.append(drug)
    data["drugs"] = normalized

    if not isinstance(data.get("patient"), dict):
        data["patient"] = {}

    result = Prescription(**data)
    logger.info(f"处方解析成功: {len(result.drugs)}种药物")
    return result
