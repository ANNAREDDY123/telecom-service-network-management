from fastapi.testclient import TestClient

from app.main import app
from app.middleware.security_middleware import (
    InMemoryRateLimiter,
    get_client_identifier,
    is_auth_endpoint,
    rate_limiter,
    auth_rate_limiter,
)


client = TestClient(app)


def test_health_endpoint():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_readiness_endpoint():

    response = client.get(
        "/ready"
    )

    assert response.status_code in {
        200,
        503,
    }

    data = response.json()

    assert "status" in data
    assert "database" in data


def test_security_headers():

    response = client.get(
        "/health"
    )

    assert (
        response.headers[
            "X-Content-Type-Options"
        ]
        == "nosniff"
    )

    assert (
        response.headers[
            "X-Frame-Options"
        ]
        == "DENY"
    )

    assert (
        response.headers[
            "Referrer-Policy"
        ]
        == "strict-origin-when-cross-origin"
    )

    assert (
        "frame-ancestors 'none'"
        in response.headers[
            "Content-Security-Policy"
        ]
    )

    assert (
        "camera=()"
        in response.headers[
            "Permissions-Policy"
        ]
    )


def test_request_id_is_added():

    response = client.get(
        "/health"
    )

    assert (
        "X-Request-ID"
        in response.headers
    )

    assert (
        len(
            response.headers[
                "X-Request-ID"
            ]
        )
        > 0
    )


def test_custom_request_id_is_preserved():

    request_id = (
        "level20-test-request"
    )

    response = client.get(
        "/health",
        headers={
            "X-Request-ID": request_id
        },
    )

    assert (
        response.headers[
            "X-Request-ID"
        ]
        == request_id
    )


def test_auth_endpoint_detection():

    assert is_auth_endpoint(
        "/auth/login"
    )

    assert is_auth_endpoint(
        "/auth/register"
    )

    assert is_auth_endpoint(
        "/auth/refresh"
    )

    assert not is_auth_endpoint(
        "/customers"
    )


def test_client_identifier():

    limiter_request = client.get(
        "/health"
    )

    assert limiter_request.status_code == 200

    # The helper must safely handle requests where
    # client information is unavailable.
    result = get_client_identifier(
        limiter_request.request
    )

    assert result in {
        "unknown",
        "testclient",
        "127.0.0.1",
    }


def test_rate_limiter_allows_requests():

    limiter = InMemoryRateLimiter(
        max_requests=2,
        window_seconds=60,
    )

    assert limiter.is_allowed(
        "test-client"
    )

    assert limiter.is_allowed(
        "test-client"
    )


def test_rate_limiter_blocks_excess_requests():

    limiter = InMemoryRateLimiter(
        max_requests=2,
        window_seconds=60,
    )

    assert limiter.is_allowed(
        "test-client"
    )

    assert limiter.is_allowed(
        "test-client"
    )

    assert not limiter.is_allowed(
        "test-client"
    )


def test_rate_limiter_separates_clients():

    limiter = InMemoryRateLimiter(
        max_requests=1,
        window_seconds=60,
    )

    assert limiter.is_allowed(
        "client-a"
    )

    assert limiter.is_allowed(
        "client-b"
    )

    assert not limiter.is_allowed(
        "client-a"
    )


def test_rate_limiter_reset():

    limiter = InMemoryRateLimiter(
        max_requests=1,
        window_seconds=60,
    )

    assert limiter.is_allowed(
        "client-a"
    )

    assert not limiter.is_allowed(
        "client-a"
    )

    limiter.reset()

    assert limiter.is_allowed(
        "client-a"
    )


def test_global_rate_limit_configuration():

    assert (
        rate_limiter.max_requests
        == 100
    )

    assert (
        rate_limiter.window_seconds
        == 60
    )


def test_auth_rate_limit_configuration():

    assert (
        auth_rate_limiter.max_requests
        == 10
    )

    assert (
        auth_rate_limiter.window_seconds
        == 60
    )


def test_options_request_has_cors_headers():

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code in {
        200,
        400,
    }

    if response.status_code == 200:
        assert (
            "access-control-allow-origin"
            in response.headers
        )


def test_unknown_route_still_gets_security_headers():

    response = client.get(
        "/this-route-does-not-exist"
    )

    assert response.status_code == 404

    assert (
        response.headers[
            "X-Content-Type-Options"
        ]
        == "nosniff"
    )

    assert (
        response.headers[
            "X-Frame-Options"
        ]
        == "DENY"
    )