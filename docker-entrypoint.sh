#!/bin/bash
set -e

echo "🚀 启动智能用药安全审查系统..."

# 启动 FastAPI 后台
echo "📡 启动 FastAPI 服务 (端口 8000)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# 等待 API 就绪
sleep 3

# 启动 Streamlit 前台
echo "🖥️ 启动 Streamlit 前端 (端口 8501)..."
streamlit run streamlit_app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false &
UI_PID=$!

# 捕获退出信号
trap "kill $API_PID $UI_PID; exit 0" SIGTERM SIGINT

# 等待任一进程退出
wait -n $API_PID $UI_PID
