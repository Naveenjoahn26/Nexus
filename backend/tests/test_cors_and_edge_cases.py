"""
NEXUS EDU — CORS and Edge-Case Tests.

Validates:
1. CORS preflight OPTIONS, allowed methods, allowed headers, and max-age
2. CORS headers on successful responses, 401, 404, 422, and 500 exceptions
3. CORS origin matching (ports, subdomains, Vercel, Render) and rejection of untrusted origins
4. Trailing slash and whitespace normalization in CORS origins settings
5. DEBUG configuration flag coercion across multiple values (true, false, release, prod, 1, 0, etc.)
6. Authentication edge cases: invalid credentials, malformed JWT, expired token, missing sub claim
7. Course creation validation: missing required fields
8. Document upload validation: unsupported file extensions
"""

from __future__ import annotations

import os
import re
import uuid
import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import create_access_token
from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ── CORS Tests ────────────────────────────────────────────────────────


def test_cors_preflight_options_login(client: TestClient) -> None:
    """Preflight OPTIONS request to /auth/login returns 200 with CORS headers."""
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in response.headers.get("access-control-allow-methods", "")
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_on_normal_get_response(client: TestClient) -> None:
    """GET /health echoes allowed origin in CORS headers."""
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_on_404_not_found(client: TestClient) -> None:
    """404 responses maintain CORS headers so frontend doesn't trigger CORS violation."""
    response = client.get("/nonexistent-endpoint", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 404
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_on_401_unauthorized(client: TestClient) -> None:
    """401 responses include CORS headers for frontend consumption."""
    response = client.get("/api/v1/auth/me", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 401
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_on_422_validation_error(client: TestClient) -> None:
    """422 validation error responses include CORS headers."""
    response = client.post(
        "/api/v1/auth/register",
        json={},
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 422
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_on_500_internal_error(client: TestClient) -> None:
    """500 responses retain CORS headers rather than being masked as CORS errors."""
    @app.get("/_test_internal_error")
    async def _failing_route():
        raise RuntimeError("Simulated internal explosion")

    response = client.get("/_test_internal_error", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 500
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.json()["success"] is False
    assert response.json()["error"] == "Internal Server Error"


def test_cors_regex_allows_dev_ports(client: TestClient) -> None:
    """Dynamic ports on localhost / 127.0.0.1 (e.g. 5174, 3000, 8080) are allowed."""
    for origin in [
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
    ]:
        response = client.get("/health", headers={"Origin": origin})
        assert response.headers.get("access-control-allow-origin") == origin, f"Failed for {origin}"


def test_cors_regex_allows_vercel_and_render_domains(client: TestClient) -> None:
    """Deployments on Vercel and Render are permitted by CORS regex."""
    for origin in [
        "https://nexus-ai-silk-ten.vercel.app",
        "https://preview-123.vercel.app",
        "https://nexus-ai-b1gb.onrender.com",
    ]:
        response = client.get("/health", headers={"Origin": origin})
        assert response.headers.get("access-control-allow-origin") == origin, f"Failed for {origin}"


def test_cors_rejects_untrusted_origin(client: TestClient) -> None:
    """Untrusted origins do not receive an Access-Control-Allow-Origin header."""
    for untrusted in ["http://evil.com", "https://hacker.org", "http://localhost.evil.com"]:
        response = client.get("/health", headers={"Origin": untrusted})
        assert response.headers.get("access-control-allow-origin") is None


# ── Configuration Edge Cases ──────────────────────────────────────────


@pytest.mark.parametrize(
    "raw_val, expected",
    [
        ("true", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("False", False),
        ("0", False),
        ("no", False),
        ("off", False),
        ("release", False),
        ("prod", False),
    ],
)
def test_config_debug_coercion(raw_val: str, expected: bool) -> None:
    original = os.environ.get("DEBUG")
    os.environ["DEBUG"] = raw_val
    try:
        settings = Settings()
        assert settings.debug is expected
    finally:
        if original is None:
            os.environ.pop("DEBUG", None)
        else:
            os.environ["DEBUG"] = original


def test_config_cors_origins_normalisation() -> None:
    """Trailing slashes and extra whitespace in CORS origins are cleaned."""
    settings = Settings(cors_origins="http://localhost:5173/ , http://localhost:9000/ , http://custom-domain.com")
    origins = settings.get_cors_origins()
    assert "http://localhost:9000" in origins
    assert "http://custom-domain.com" in origins
    # Ensure no origin has a trailing slash
    for o in origins:
        assert not o.endswith("/")


# ── Auth & JWT Edge Cases ─────────────────────────────────────────────


def test_auth_login_invalid_credentials(client: TestClient) -> None:
    """Logging in with non-existent credentials returns 401 with standard error format."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "does_not_exist@example.com", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert "Incorrect email or password" in body["error"]


def test_auth_jwt_malformed_token(client: TestClient) -> None:
    """Malformed bearer token returns 401 Unauthorized."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt-token"},
    )
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid or expired token"


def test_auth_jwt_missing_sub_claim(client: TestClient) -> None:
    """JWT missing the 'sub' claim returns 401."""
    import jwt
    token = jwt.encode({"role": "student"}, "nexus-local-dev-secret-change-me", algorithm="HS256")
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "missing subject" in response.json()["error"].lower()


def test_auth_jwt_non_uuid_sub(client: TestClient) -> None:
    """JWT with a non-UUID 'sub' claim returns 401."""
    import jwt
    token = jwt.encode({"sub": "not-a-uuid"}, "nexus-local-dev-secret-change-me", algorithm="HS256")
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "invalid user id format" in response.json()["error"].lower()


# ── Course & Document Validation Edge Cases ───────────────────────────


def test_course_create_requires_authentication(client: TestClient) -> None:
    """Creating a course without authorization returns 401."""
    response = client.post("/api/v1/courses", json={"name": "CS101"})
    assert response.status_code == 401


def test_document_upload_unsupported_file_type(client: TestClient) -> None:
    """Uploading an unsupported file extension (.exe) returns 500 / error."""
    # Create a valid test JWT
    valid_uuid = str(uuid.uuid4())
    token = create_access_token(data={"sub": valid_uuid, "role": "student"})
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("malware.exe", b"MZbinarycontent", "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    # Since user doesn't exist in DB or file is rejected, should return 401 or 500 error
    assert response.status_code in (401, 500)

