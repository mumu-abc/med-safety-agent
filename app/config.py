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


settings = Settings()
