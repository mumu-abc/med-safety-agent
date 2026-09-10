"""Pydantic 数据模型"""

from pydantic import BaseModel, Field


class PatientInfo(BaseModel):
    """患者信息（与 prescription_agent.PatientInfo 保持一致）"""
    age: int | None = Field(default=None, description="患者年龄")
    gender: str = Field(default="", description="患者性别")
    conditions: list[str] = Field(default_factory=list, description="患者基础疾病")
    allergies: list[str] = Field(default_factory=list, description="已知过敏")
    renal_function: str = Field(default="normal", description="肾功能: normal/impaired/unknown")
    liver_function: str = Field(default="normal", description="肝功能: normal/impaired/unknown")
    pregnancy: str = Field(default="no", description="是否怀孕: yes/no/unknown")


class Drug(BaseModel):
    """处方药物（与 prescription_agent.DrugItem 保持一致）"""
    name: str
    dosage: str = ""
    frequency: str = ""
    duration: str = ""
    indication: str = ""


class Prescription(BaseModel):
    """解析后的处方"""
    diagnosis: str = ""
    drugs: list[Drug] = Field(default_factory=list)
    patient: PatientInfo = Field(default_factory=PatientInfo)


class RiskItem(BaseModel):
    """单条风险"""
    drug: str = ""
    risk_type: str = ""
    severity: str = "high"
    description: str
    source: str = "llm"
    suggestion: str = ""


class RiskAssessment(BaseModel):
    """风险评估结果（与 risk_agent.RiskAssessment 保持一致）"""
    overall_risk: str = Field(default="unknown", description="总体风险等级: critical/high/medium/low/safe")
    risks: list[RiskItem] = Field(default_factory=list)
    summary: str = ""


class InteractionItem(BaseModel):
    """药物交互"""
    drug_a: str
    drug_b: str
    severity: str = "medium"
    mechanism: str = ""
    suggestion: str = ""


class ContraindicationItem(BaseModel):
    """禁忌症"""
    drug: str
    condition: str
    severity: str = "high"
    suggestion: str = ""


class InteractionReport(BaseModel):
    """交互检测结果"""
    interactions: list[InteractionItem] = Field(default_factory=list)
    contraindications: list[ContraindicationItem] = Field(default_factory=list)
    analysis: str = ""


class AlternativeDrug(BaseModel):
    """替代药物（与 alternative_agent.AlternativeDrug 保持一致）"""
    name: str
    category: str = ""
    reason: str = ""


class AlternativeSuggestion(BaseModel):
    """替代建议（与 alternative_agent.AlternativeSuggestion 保持一致）"""
    original_drug: str = ""
    alternatives: list[AlternativeDrug] = Field(default_factory=list)
    reason: str = ""


class AlternativeReport(BaseModel):
    """替代方案结果（与 alternative_agent.AlternativeReport 保持一致）"""
    suggestions: list[AlternativeSuggestion] = Field(default_factory=list)
    summary: str = ""


class StepResult(BaseModel):
    """单步结果（SSE 用）"""
    status: str = "ok"
    risks: list[RiskItem] = Field(default_factory=list)
    interactions: list[InteractionItem] = Field(default_factory=list)
    contraindications: list[ContraindicationItem] = Field(default_factory=list)
    alternatives: list[AlternativeSuggestion] = Field(default_factory=list)
    prescriptions: list[Drug] = Field(default_factory=list)
    summary: str = ""


class ReviewResponse(BaseModel):
    """审查结果响应"""
    prescription: Prescription = Field(default_factory=Prescription)
    risk_assessment: RiskAssessment = Field(default_factory=RiskAssessment)
    interactions: list[InteractionItem] = Field(default_factory=list)
    contraindications: list[ContraindicationItem] = Field(default_factory=list)
    alternatives: list[AlternativeSuggestion] = Field(default_factory=list)
    report: str = ""
    workflow_state: str = "completed"
    error: str = ""


# 前端 SSE 事件格式
class SSEEvent(BaseModel):
    """SSE 事件（前端 handleSSEEvent 格式）"""
    node: str
    status: str  # running | completed | error
    result: StepResult = Field(default_factory=StepResult)
