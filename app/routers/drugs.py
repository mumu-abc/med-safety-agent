"""药物查询API。"""
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.graph.drug_graph import (
    get_all_drugs, get_drug_by_name, get_stats, find_interactions,
    find_shortest_path, find_drug_communities, analyze_interaction_chain,
    get_all_interactions,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/drugs", tags=["药物"])


@router.get("")
async def list_drugs():
    """获取所有药物列表。"""
    try:
        return {"drugs": get_all_drugs()}
    except Exception as e:
        logger.exception("获取药物列表失败")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/search")
async def search_drug(name: str):
    """按名称搜索药物。"""
    try:
        drug = get_drug_by_name(name)
        if drug:
            return drug
        return JSONResponse(status_code=404, content={"error": f"未找到药物: {name}"})
    except Exception as e:
        logger.exception("搜索药物失败")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/stats")
async def drug_stats():
    """获取图谱统计信息。"""
    try:
        return get_stats()
    except Exception as e:
        logger.exception("获取统计信息失败")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/all-interactions")
async def all_interactions():
    """获取全部药物相互作用(用于图谱可视化)。"""
    try:
        return {"interactions": get_all_interactions()}
    except Exception as e:
        logger.exception("获取全部交互失败")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/interactions")
async def check_interactions(drug_names: list[str]):
    """查询药物相互作用。输入药品名称列表,内部转换为ID查询图谱。"""
    try:
        ids = []
        for name in drug_names:
            drug = get_drug_by_name(name)
            if drug:
                ids.append(drug["id"])
        return {"interactions": find_interactions(ids)}
    except Exception as e:
        logger.exception("查询相互作用失败")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/path")
async def shortest_path(drug_a: str, drug_b: str):
    """查找两个药物之间的最短交互路径(多跳推理)。"""
    try:
        path = find_shortest_path(drug_a, drug_b)
        if path:
            return {"path": path, "hops": len(path) - 1}
        return {"path": None, "message": f"未找到 {drug_a} 到 {drug_b} 的交互路径"}
    except Exception as e:
        logger.exception("查找最短路径失败")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/communities")
async def drug_communities():
    """药物社区发现——基于交互关系的聚类分析。"""
    try:
        communities = find_drug_communities()
        return {"communities": communities, "count": len(communities)}
    except Exception as e:
        logger.exception("社区发现失败")
        return JSONResponse(status_code=500, content={"error": str(e)})


class ChainRequest(BaseModel):
    drug_names: list[str]


@router.post("/interaction-chain")
async def interaction_chain(req: ChainRequest):
    """多药联用交互链分析(环路检测、代谢冲突、交互密度)。"""
    try:
        return analyze_interaction_chain(req.drug_names)
    except Exception as e:
        logger.exception("交互链分析失败")
        return JSONResponse(status_code=500, content={"error": str(e)})
