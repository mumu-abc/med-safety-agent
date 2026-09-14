#!/bin/bash
set -e

echo "🚀 启动智能用药安全审查系统..."

# 前端是原生 HTML/JS 单页应用,由 FastAPI 直接静态托管在同一端口(8000)。
# 早期版本在这里额外拉起一个 Streamlit 进程(8501),现已统一为单前端:
# 容器内只保留一个服务进程,用 exec 让它直接接管 PID 1,
# 这样 Docker 的 SIGTERM 能正确传递到 uvicorn,健康检查也只需要探一个端口。
echo "📡 启动 FastAPI 服务 (端口 8000)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
