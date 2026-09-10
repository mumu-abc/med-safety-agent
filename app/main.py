"""FastAPI 入口:智能用药安全审查系统。"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# P2-22:统一日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

from app.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="智能用药安全审查系统",
    description="多Agent协作的用药安全审查,含药物知识图谱、规则引擎、风险评估",
    version="1.0.0",
)

# 轻量 IP 限流:只保护 /api/review/* 与 /api/eval/run,静态资源不限流
# 注意:Starlette 里后注册的中间件在外层,所以限流必须先注册,让 CORS 成为最外层,
# 否则 429 响应不会带 CORS 头,跨域调用方只能看到 CORS 错误而不是限流提示。
app.add_middleware(RateLimitMiddleware)

# P2-14修复:allow_origins=["*"] + allow_credentials=True 违反CORS规范
# 前端同源部署,不需要credentials;若需跨域认证改为具体origin列表
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- API 根路由(必须在 mount 之前定义,否则被静态文件拦截) ----

@app.get("/api")
async def root():
    return {
        "name": "智能用药安全审查系统",
        "description": "药物知识图谱 + 规则引擎 + LLM推理",
        "docs": "/docs",
        "endpoints": {
            "review": "/api/review",
            "drugs": "/api/drugs",
            "patients": "/api/patients",
            "evaluation": "/api/eval",
        },
    }


@app.get("/api/health")
async def health():
    """系统健康检查:探活关键依赖,而不是只返回 alive。"""
    from app.config import settings
    from app.database import get_db
    from app.graph.repository import get_repository

    checks: dict[str, bool] = {}
    try:
        checks["llm_configured"] = bool(settings.llm_api_key)
    except Exception:
        checks["llm_configured"] = False
    try:
        checks["drug_graph_loaded"] = bool(get_repository().graph.number_of_nodes())
    except Exception as e:
        logging.warning(f"健康检查: 知识图谱未就绪 -> {e}")
        checks["drug_graph_loaded"] = False
    try:
        get_db().get_cache_stats()
        checks["database_ok"] = True
    except Exception as e:
        logging.warning(f"健康检查: 数据库不可用 -> {e}")
        checks["database_ok"] = False

    return {
        "status": "ok" if all(checks.values()) else "degraded",
        "checks": checks,
        "version": "1.0.0",
    }


# ---- 注册路由 ----

from app.routers.review import router as review_router
from app.routers.drugs import router as drugs_router
from app.routers.patients import router as patients_router
from app.routers.evaluation import router as eval_router

app.include_router(review_router)
app.include_router(drugs_router)
app.include_router(patients_router)
app.include_router(eval_router)

# ---- 前端静态文件(必须最后 mount,否则拦截所有路由) ----

frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
