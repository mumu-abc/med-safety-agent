"""处方解析Agent:用 LLM + JSON 手动解析从自由文本提取结构化处方。

面试要点:
1. with_structured_output 强约束输出格式,不会返回乱七八糟的文本。
2. Pydantic schema 就是"合同"——LLM必须按这个格式输出。
3. 同时提取患者信息(年龄/性别/肝肾功能/过敏史),为后续风险评估提供输入。
"""
import json
import logging
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from app.llm import get_llm

logger = logging.getLogger(__name__)


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


def parse_prescription(text: str) -> Prescription:
    """从自由文本解析结构化处方。手动解析JSON输出。"""
    try:
        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content=PARSE_SYSTEM),
            HumanMessage(content=f"处方文本:\n{text}"),
        ])
        content = response.content
        logger.info(f"MiMo原始返回: {repr(content[:500])}")
        content = content.strip() if content else ""
        # 去掉可能的 markdown 代码块标记
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

        # 清理 JSON 中的 null 值,替换为空字符串(Pydantic str 字段不接受 null)
        import re
        content = re.sub(r':\s*null', ': ""', content)

        data = json.loads(content)
        # 确保 drugs 列表中的每个项都有必需字段
        for drug in data.get("drugs", []):
            drug.setdefault("name", "")
            drug.setdefault("dosage", "")
            drug.setdefault("frequency", "")
            drug.setdefault("duration", "")
        result = Prescription(**data)
        logger.info(f"处方解析成功: {len(result.drugs)}种药物")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"处方解析JSON解析失败: {e}, 原始输出: {content[:200]}")
        return Prescription(diagnosis="", drugs=[], patient=PatientInfo())
    except Exception as e:
        logger.error(f"处方解析失败: {e}")
        return Prescription(diagnosis="", drugs=[], patient=PatientInfo())
