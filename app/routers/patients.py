"""患者档案API。"""
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.graph.patient_store import get_patient, save_patient, list_patients

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/patients", tags=["患者"])


class PatientData(BaseModel):
    name: str = ""
    age: int | None = None
    gender: str = ""
    conditions: list[str] = []
    allergies: list[str] = []
    liver_function: str = "normal"
    renal_function: str = "normal"
    pregnancy: str = "no"


@router.get("")
async def get_patients():
    """获取所有患者列表。"""
    try:
        return {"patients": list_patients()}
    except Exception as e:
        logger.exception("获取患者列表失败")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/{patient_id}")
async def get_patient_by_id(patient_id: str):
    """获取患者详情。"""
    try:
        patient = get_patient(patient_id)
        if patient:
            return patient
        return JSONResponse(status_code=404, content={"error": f"未找到患者: {patient_id}"})
    except Exception as e:
        logger.exception("获取患者详情失败")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.put("/{patient_id}")
async def update_patient(patient_id: str, data: PatientData):
    """创建或更新患者档案。"""
    try:
        save_patient(patient_id, data.model_dump())
        return {"message": "保存成功", "patient_id": patient_id}
    except Exception as e:
        logger.exception("保存患者档案失败")
        return JSONResponse(status_code=500, content={"error": str(e)})
