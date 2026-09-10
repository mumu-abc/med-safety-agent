"""轻量 IP 限流中间件。

设计取舍:
- 只保护"昂贵"端点(/api/review/*、/api/eval/run),静态资源和查询类接口不限流,
  避免前端加载 index.html/图片被误伤。
- 进程内滑动窗口,零外部依赖(Redis 对单机 demo 是过度设计)。
- 生产多实例部署时,窗口按实例独立;如需全局限流再换 Redis 后端。
"""
import os
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


# 是否部署在可信反向代理之后。默认 false —— X-Forwarded-For 由客户端提供,
# 默认信任等于任何人换个 header 就能重置配额,限流形同虚设。
TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true"


class _SlidingWindow:
    """线程安全的滑动窗口计数器(带定期清理,避免 key 无限增长)。"""

    CLEANUP_INTERVAL = 300.0  # 每 5 分钟清一次空桶

    def __init__(self):
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()
        self._next_cleanup = time.monotonic() + self.CLEANUP_INTERVAL

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
            # 定期回收长期无请求的 IP 桶,否则公网暴露后会一直膨胀
            if now >= self._next_cleanup:
                self._next_cleanup = now + self.CLEANUP_INTERVAL
                for k in [k for k, v in self._hits.items() if not v]:
                    del self._hits[k]
            return True


_window = _SlidingWindow()


def _client_ip(request: Request) -> str:
    """取客户端 IP。

    X-Forwarded-For 是请求头,客户端可以随意伪造;只有确实部署在可信反向代理
    之后(设置 TRUST_PROXY_HEADERS=true)才读取,且取**最右侧**那一跳 ——
    代理会在转发时追加真实地址,最右侧才是代理写入的、无法被客户端伪造的值。
    """
    if TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[-1].strip()
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
