"""LangSmith 接线方式的回归守卫。

背景(真实踩过的坑):
自检脚本能查到单次 LLM 调用被记录了,于是以为"可观测性已配好";
但打开 LangSmith 一看,项目里**一个流水线 trace 都没有**,只有孤立的一次
`ChatOpenAI` 调用。

根因:`_setup_langsmith()` 原先只在 `get_llm()` 里懒调用。而 tracing 开关是在
「一次 run 开始时」读环境变量的,于是时序变成:

    1. graph.invoke() 开始        -> 环境里还没开关,LangGraph 不建根 run
    2. 执行到 node_parse 调 LLM   -> 这时才把 LANGSMITH_TRACING=true 写进环境
    3. LLM 调用被记录,但没有父节点 -> 孤立根节点,看不到 parse→...→report 结构

所以 `_setup_langsmith()` 必须在**模块导入时**执行。下面的用例守住这一点。
"""
import importlib
import os

import app.llm as llm_mod

_ENV_KEYS = (
    "LANGSMITH_TRACING",
    "LANGSMITH_API_KEY",
    "LANGSMITH_PROJECT",
    "LANGSMITH_ENDPOINT",
    "LANGCHAIN_TRACING_V2",
)


def _restore(snapshot: dict) -> None:
    """还原 tracing 环境变量,并按真实配置重新导入一次模块。"""
    for key, val in snapshot.items():
        if val is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = val
    importlib.reload(llm_mod)


def test_tracing_env_set_when_module_imported(monkeypatch):
    """导入 app.llm 就应写好 tracing 环境变量 —— 不能等到调用 get_llm()。"""
    snapshot = {k: os.environ.get(k) for k in _ENV_KEYS}
    try:
        for key in _ENV_KEYS:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setattr(llm_mod.settings, "langsmith_tracing", True)
        monkeypatch.setattr(llm_mod.settings, "langsmith_api_key", "test-key-not-real")
        monkeypatch.setattr(llm_mod.settings, "langsmith_project", "test-project")

        importlib.reload(llm_mod)  # 等价于「进程首次 import app.llm」

        assert os.environ.get("LANGSMITH_TRACING") == "true"
        assert os.environ.get("LANGSMITH_API_KEY") == "test-key-not-real"
        assert os.environ.get("LANGSMITH_PROJECT") == "test-project"
        # 兼容旧变量名,部分 langgraph 版本只认这个
        assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    finally:
        _restore(snapshot)


def test_no_tracing_without_api_key(monkeypatch):
    """没配 key 时不应打开 tracing,否则会产生大量鉴权失败的垃圾请求。"""
    snapshot = {k: os.environ.get(k) for k in _ENV_KEYS}
    try:
        for key in _ENV_KEYS:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setattr(llm_mod.settings, "langsmith_tracing", True)
        monkeypatch.setattr(llm_mod.settings, "langsmith_api_key", "")

        importlib.reload(llm_mod)

        assert "LANGSMITH_TRACING" not in os.environ
        assert "LANGCHAIN_TRACING_V2" not in os.environ
    finally:
        _restore(snapshot)


def test_no_tracing_when_switch_off(monkeypatch):
    """开关关掉时同样不应写入环境变量。"""
    snapshot = {k: os.environ.get(k) for k in _ENV_KEYS}
    try:
        for key in _ENV_KEYS:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setattr(llm_mod.settings, "langsmith_tracing", False)
        monkeypatch.setattr(llm_mod.settings, "langsmith_api_key", "test-key-not-real")

        importlib.reload(llm_mod)

        assert "LANGSMITH_TRACING" not in os.environ
    finally:
        _restore(snapshot)
