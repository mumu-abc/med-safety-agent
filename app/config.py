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
    llm_base_url: str = "https://token-plan-cn.xiaomimimo.com/v1"
    llm_api_key: str = ""
    llm_model: str = "mimo-v2.5-pro"
    llm_temperature: float = 0.0

    # ---- LangSmith Observability ----
    langsmith_api_key: str = ""
    langsmith_project: str = "med-safety-agent"
    langsmith_tracing: bool = False

    # ---- 知识图谱 ----
    graph_path: str = str(BASE_DIR / "data" / "drug_graph.json")


settings = Settings()
