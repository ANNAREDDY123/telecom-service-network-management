from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityConfig:
    # CORS
    allowed_origins: tuple[str, ...] = (
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    )

    allowed_methods: tuple[str, ...] = (
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    )

    allowed_headers: tuple[str, ...] = (
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Request-ID",
    )

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Authentication endpoints are intentionally stricter.
    auth_rate_limit_requests: int = 10
    auth_rate_limit_window_seconds: int = 60


security_config = SecurityConfig()