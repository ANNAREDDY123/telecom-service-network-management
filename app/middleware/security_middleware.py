import time
import uuid
from collections import defaultdict
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.security_config import security_config


class InMemoryRateLimiter:
    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(list)
        self._lock = Lock()

    def is_allowed(
        self,
        key: str,
    ) -> bool:

        now = time.monotonic()
        window_start = (
            now - self.window_seconds
        )

        with self._lock:
            timestamps = self._requests[key]

            while (
                timestamps
                and timestamps[0] <= window_start
            ):
                timestamps.pop(0)

            if len(timestamps) >= self.max_requests:
                return False

            timestamps.append(now)

            return True

    def reset(self):
        with self._lock:
            self._requests.clear()


rate_limiter = InMemoryRateLimiter(
    max_requests=security_config.rate_limit_requests,
    window_seconds=security_config.rate_limit_window_seconds,
)

auth_rate_limiter = InMemoryRateLimiter(
    max_requests=security_config.auth_rate_limit_requests,
    window_seconds=(
        security_config.auth_rate_limit_window_seconds
    ),
)


def get_client_identifier(
    request: Request,
) -> str:

    client = getattr(
        request,
        "client",
        None,
    )

    if client is not None:
        host = getattr(
            client,
            "host",
            None,
        )

        if host:
            return host

    return "unknown"


def is_auth_endpoint(
    path: str,
) -> bool:

    normalized = path.rstrip("/")

    return normalized in {
        "/auth/login",
        "/auth/register",
        "/auth/refresh",
    }


async def security_middleware(
    request: Request,
    call_next,
):

    request_id = (
        request.headers.get("X-Request-ID")
        or str(uuid.uuid4())
    )

    request.state.request_id = request_id

    client_id = get_client_identifier(
        request
    )

    limiter = (
        auth_rate_limiter
        if is_auth_endpoint(
            request.url.path
        )
        else rate_limiter
    )

    rate_limit_key = (
        f"{client_id}:"
        f"{request.url.path}"
    )

    if not limiter.is_allowed(
        rate_limit_key
    ):
        response = JSONResponse(
            status_code=429,
            content={
                "detail": (
                    "Too many requests. "
                    "Please try again later."
                )
            },
        )

        response.headers[
            "Retry-After"
        ] = str(
            limiter.window_seconds
        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        return response

    response = await call_next(request)

    response.headers[
        "X-Request-ID"
    ] = request_id

    # ---------------------------------------------------------
    # Security headers
    # ---------------------------------------------------------

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "DENY"

    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    response.headers[
        "Permissions-Policy"
    ] = (
        "camera=(), microphone=(), "
        "geolocation=()"
    )

    response.headers[
        "Content-Security-Policy"
    ] = (
        "default-src 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none';"
    )

    # HSTS is appropriate only when HTTPS is being used.
    # We therefore do not add it to local HTTP development
    # responses.

    return response