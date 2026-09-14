"""项目配置。"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- LLM ----
    # 默认值与 .env / .env.example 保持一致(智谱 GLM),避免没有 .env 时回退到旧模型
    llm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    llm_api_key: str = ""
    llm_model: str = "glm-4-flash"
    llm_temperature: float = 0.0

    # ---- LangSmith Observability ----
    langsmith_api_key: str = ""
    langsmith_project: str = "med-safety-agent"
    langsmith_tracing: bool = False

    # ---- 知识图谱 ----
    graph_path: str = str(BASE_DIR / "data" / "drug_graph.json")

    # ---- 交互检测模式 ----
    # graph: 确定性图谱直查(默认,毫秒级,安全兜底)
    # react: LLM ReAct 工具循环(慢,用于演示/补充语义分析)
    detect_mode: str = "graph"

    # ---- 风险评估模式 ----
    # semantic: 单次 structured output(默认,延迟可控)
    # react: ReAct 工具循环(慢);失败自动降级 semantic
    # rules: 纯图谱+规则,不调 LLM
    risk_mode: str = "semantic"

    # ---- 记忆系统(向量检索) ----
    # 依赖 sentence-transformers + faiss,首次调用会下载 bge-small-zh 模型(约 400MB)
    # 并常驻占用数百 MB 内存。公网免费层(Render 512MB / Railway 500MB)会直接 OOM,
    # 部署时设 ENABLE_MEMORY=false 关闭,核心审查链路(图谱+规则+LLM)不受影响。
    enable_memory: bool = True


settings = Settings()
