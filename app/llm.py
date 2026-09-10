"""LLM 工厂:支持 LangSmith 可观测性追踪。

面试要点:
1. 通过环境变量启用 LangSmith tracing,自动追踪每次 LLM 调用和工具调用链。
2. 在 LangSmith UI 可查看 ReAct 循环的每步推理、工具输入输出、延迟。
3. 用于调试 prompt、定位工具调用异常、对比不同模型的推理质量。
"""
import os
import threading
from langchain_openai import ChatOpenAI
from app.config import settings

_llm = None
_lock = threading.Lock()


def _setup_langsmith():
    """配置 LangSmith 环境变量,启用 tracing。"""
    if settings.langsmith_tracing and settings.langsmith_api_key:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
        os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"


def get_llm() -> ChatOpenAI:
    """获取 LLM 实例(线程安全单例)。"""
    global _llm
    if _llm is not None:
        return _llm
    with _lock:
        if _llm is not None:
            return _llm
        _setup_langsmith()
        _llm = ChatOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_retries=3,
            # 单次调用 120s 对 glm-4-flash 已足够宽松;原来是 300s,叠加 3 次重试
            # 最坏要 15 分钟才失败,而 SSE 早已超时断开,白白占用线程和 token。
            timeout=120,
        )
    return _llm
