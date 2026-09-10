"""启动脚本:FastAPI(8002)。"""
import subprocess
import sys
import time
import webbrowser
import socket

FASTAPI_PORT = 8002


def is_port_in_use(port: int) -> bool:
    """检查端口是否已被占用。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    """启动 FastAPI 后端并自动打开浏览器。"""
    print("=" * 50)
    print("💊 智能用药安全审查系统")
    print("=" * 50)

    # 检查端口是否已占用
    if is_port_in_use(FASTAPI_PORT):
        print(f"\n⚠️  端口 {FASTAPI_PORT} 已被占用（服务可能已在运行）")
        print(f"   直接打开浏览器: http://127.0.0.1:{FASTAPI_PORT}")
        webbrowser.open(f"http://127.0.0.1:{FASTAPI_PORT}")
        return

    # 启动 FastAPI
    print(f"\n🚀 启动 FastAPI 后端 (端口 {FASTAPI_PORT})...")
    fastapi_cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--host", "127.0.0.1",
        "--port", str(FASTAPI_PORT),
    ]
    fastapi_proc = subprocess.Popen(fastapi_cmd)

    # 等待 FastAPI 启动
    time.sleep(3)

    # 自动打开浏览器
    frontend_url = f"http://127.0.0.1:{FASTAPI_PORT}"
    print(f"\n✅ 启动完成!")
    print(f"   - 前端界面: {frontend_url}")
    print(f"   - API文档:  {frontend_url}/docs")
    print(f"\n🌐 正在打开浏览器: {frontend_url}")
    webbrowser.open(frontend_url)

    print("\n按 Ctrl+C 停止服务...")
    try:
        fastapi_proc.wait()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        fastapi_proc.terminate()
        print("✅ 已停止")


if __name__ == "__main__":
    main()
