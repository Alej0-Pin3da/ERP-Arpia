import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_counters: dict[str, int] = defaultdict(int)
_errors: dict[str, int] = defaultdict(int)
_latencies: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def record(path: str, latency_ms: float, is_error: bool) -> None:
    with _lock:
        _counters[path] += 1
        if is_error:
            _errors[path] += 1
        lst = _latencies[path]
        lst.append(latency_ms)
        if len(lst) > 200:
            lst.pop(0)


def snapshot() -> dict:
    with _lock:
        out = {}
        for k, v in _counters.items():
            lat = _latencies[k]
            avg = sum(lat) / len(lat) if lat else 0
            p95 = sorted(lat)[int(len(lat) * 0.95)] if lat else 0
            out[k] = {"count": v, "errors": _errors[k], "avg_ms": round(avg, 2), "p95_ms": round(p95, 2)}
        return out


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        latency = (time.perf_counter() - start) * 1000
        path = request.url.path
        # normalize ids
        import re
        path = re.sub(r"/\d+", "/:id", path)
        is_error = response.status_code >= 400
        record(path, latency, is_error)
        response.headers["X-Response-Time-Ms"] = f"{latency:.1f}"
        return response
