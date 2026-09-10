"""
评测 API — 运行评测 + 历史查看 + 回归检测。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.database import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/eval", tags=["evaluation"])


@router.post("/run")
async def run_eval(run_name: str = Query(default="")):
    """触发一轮评测"""
    try:
        from app.evaluation import run_evaluation, detect_regressions
        result = run_evaluation()
        if run_name:
            result["run_name"] = run_name

        # 持久化
        db.save_eval_run(result)

        # 回归检测
        regression = detect_regressions(result)
        result["regression"] = regression

        return {"status": "ok", "evaluation": result}
    except Exception as e:
        logger.error(f"评测失败: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@router.get("/runs")
async def list_eval_runs(limit: int = Query(default=20, ge=1, le=100)):
    """获取历史评测列表"""
    try:
        runs = db.get_eval_runs(limit=limit)
        return {"status": "ok", "count": len(runs), "runs": runs}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/run/{run_id}")
async def get_eval_run(run_id: str):
    """获取单次评测详情"""
    try:
        run = db.get_eval_run(run_id)
        if not run:
            return JSONResponse(status_code=404, content={"status": "error", "message": "评测记录不存在"})
        return {"status": "ok", "evaluation": run}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@router.get("/latest")
async def get_latest_eval():
    """获取最近一次评测"""
    try:
        latest = db.get_latest_eval_run()
        if not latest:
            return {"status": "ok", "evaluation": None, "message": "暂无评测记录"}
        run = db.get_eval_run(latest["id"])
        return {"status": "ok", "evaluation": run}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/compare")
async def compare_evals(
    a: str = Query(..., description="基线评测 ID"),
    b: str = Query(..., description="对比评测 ID"),
):
    """对比两次评测结果"""
    try:
        from app.evaluation import detect_regressions
        run_a = db.get_eval_run(a)
        run_b = db.get_eval_run(b)
        if not run_a:
            return {"status": "error", "message": f"评测 {a} 不存在"}
        if not run_b:
            return {"status": "error", "message": f"评测 {b} 不存在"}

        comparison = detect_regressions(run_b, run_a)
        return {
            "status": "ok",
            "baseline": {"id": a, "metrics": run_a.get("metrics", {})},
            "current": {"id": b, "metrics": run_b.get("metrics", {})},
            "comparison": comparison,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


class EvalFeedbackRequest(BaseModel):
    case_desc: str
    rating: int = Field(ge=1, le=5, description="评分 1-5")
    comment: str = ""


@router.post("/feedback")
async def submit_feedback(req: EvalFeedbackRequest):
    """提交反馈"""
    try:
        fb_id = db.save_feedback(req.case_desc, req.rating, req.comment)
        return {"status": "ok", "feedback_id": fb_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/stats")
async def get_eval_stats():
    """获取评测统计摘要(总审查数/高风险数/反馈数/平均评分)。"""
    try:
        from app.routers.review import _list_reviews
        reviews = _list_reviews(n=100)
        total_reviews = len(reviews)

        feedback = db.get_recent_feedback(limit=100)
        avg_score = 0.0
        if feedback:
            avg_score = sum(f["rating"] for f in feedback) / len(feedback)

        # 统计高风险审查数
        high_risk_count = sum(1 for r in reviews if "高风险" in (r.get("result_summary") or ""))

        return {
            "total_runs": total_reviews,
            "high_risk_count": high_risk_count,
            "feedback_count": len(feedback),
            "avg_score": round(avg_score, 2),
        }
    except Exception as e:
        return {"total_runs": 0, "high_risk_count": 0, "feedback_count": 0, "avg_score": 0}


@router.get("/rules/summary")
async def get_rules_summary():
    """获取规则引擎摘要(触发次数/权重分布/误报漏报统计)"""
    try:
        from app.rules.rule_optimizer import get_rules_summary
        summary = get_rules_summary()
        return {"status": "ok", "summary": summary}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/rules/adjust")
async def adjust_rule_weight(
    rule_name: str = Query(...),
    is_false_positive: bool = Query(default=False),
    is_false_negative: bool = Query(default=False),
):
    """手动调整规则权重(误报降权/漏报升权)"""
    try:
        from app.rules.rule_optimizer import adjust_weight_from_feedback
        new_weight = adjust_weight_from_feedback(rule_name, is_false_positive, is_false_negative)
        return {"status": "ok", "rule_name": rule_name, "new_weight": new_weight}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/rules/decay")
async def decay_rule_weights():
    """触发权重衰减(所有权重向1.0回归)"""
    try:
        from app.rules.rule_optimizer import decay_weights
        decayed = decay_weights()
        return {"status": "ok", "decayed_count": len(decayed), "adjustments": decayed}
    except Exception as e:
        return {"status": "error", "message": str(e)}
