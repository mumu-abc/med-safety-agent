"""pytest 全局配置。

关键作用:测试期间关闭 LangSmith tracing。

背景:tracing 开关必须让 `app/llm.py` 在**模块导入时**就生效(否则 LangGraph 的
graph.invoke() 会在开关打开前开始执行,导致流水线没有根 trace —— 见 app/llm.py 注释)。
副作用是:测试里但凡调用过图(例如状态隔离用例会真的 invoke 一次图),
也会把 run 上传到 LangSmith,把真实审查的 trace 冲散在噪音里。

这里在 pytest 导入任何测试模块之前把开关关掉(环境变量优先级高于 .env,
所以能覆盖 .env 里的 LANGSMITH_TRACING=true)。

需要调试测试里到底发了什么请求时,可显式打开:
    LANGSMITH_TEST_TRACING=true python -m pytest tests/test_state_isolation.py
"""
import os

if os.getenv("LANGSMITH_TEST_TRACING", "false").lower() != "true":
    # 注意:必须用赋值而不是 setdefault —— 目的是覆盖 .env 里的 true
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
