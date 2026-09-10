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

# P2-14修复:allow_origins=["*"] + allow_credentials=True 违反CORS规范
# 前端同源部署,不需要credentials;若需跨域认证改为具体origin列表
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 轻量 IP 限流:只保护 /api/review/* 与 /api/eval/run,静态资源不限流
app.add_middleware(RateLimitMiddleware)


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
    """系统健康检查。"""
    from app.config import settings
    llm_configured = bool(settings.llm_api_key)
    return {
        "status": "ok",
        "llm_configured": llm_configured,
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
