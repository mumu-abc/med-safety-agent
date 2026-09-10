"""轻量 IP 限流中间件。

设计取舍:
- 只保护"昂贵"端点(/api/review/*、/api/eval/run),静态资源和查询类接口不限流,
  避免前端加载 index.html/图片被误伤。
- 进程内滑动窗口,零外部依赖(Redis 对单机 demo 是过度设计)。
- 生产多实例部署时,窗口按实例独立;如需全局限流再换 Redis 后端。
"""
import time
import threading
from collections import defaultdict, deque

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# 路径前缀 -> (窗口秒数, 窗口内最大请求数)
RULES = [
    ("/api/review", 60, 20),   # 审查接口(含 LLM 调用):60 秒内 20 次
    ("/api/eval/run", 60, 5),  # 评测触发:60 秒内 5 次
]

# 可信地址不限流(本机 / 反向代理健康检查)
WHITELIST = {"127.0.0.1", "::1", "localhost"}


class _SlidingWindow:
    """线程安全的滑动窗口计数器。"""

    def __init__(self):
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, window: int, limit: int) -> bool:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            # 清理窗口外的旧记录
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True


_window = _SlidingWindow()


def _client_ip(request: Request) -> str:
    """取客户端 IP,兼容反向代理下的 X-Forwarded-For。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # 预检请求与前端静态资源直接放行
        if request.method == "OPTIONS":
            return await call_next(request)
        # 只处理配置了规则的端点
        for prefix, window, limit in RULES:
            if path.startswith(prefix):
                ip = _client_ip(request)
                if ip in WHITELIST:
                    break
                if not _window.allow(f"{ip}:{prefix}", window, limit):
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "请求过于频繁",
                            "detail": f"{prefix} 限流:{limit} 次 / {window} 秒",
                        },
                        headers={"Retry-After": str(window)},
                    )
                break
        return await call_next(request)
