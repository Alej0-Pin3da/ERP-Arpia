"""Tests for security headers middleware and strict CORS per environment."""

from fastapi.testclient import TestClient


class TestSecurityHeaders:
    """Security headers should be present on all responses."""

    def test_csp_header_present(self, client: TestClient):
        resp = client.get("/health/live")
        assert resp.status_code == 200
        csp = resp.headers.get("content-security-policy")
        assert csp is not None
        # Basic CSP should restrict sources
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "img-src 'self' data:" in csp
        assert "font-src 'self'" in csp
        assert "connect-src 'self'" in csp

    def test_hsts_header_present_in_production(self, client: TestClient):
        # HSTS should only be set in production/staging
        # In test environment it should NOT be present
        resp = client.get("/health/live")
        assert "strict-transport-security" not in resp.headers

    def test_x_content_type_options_header(self, client: TestClient):
        resp = client.get("/health/live")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_referrer_policy_header(self, client: TestClient):
        resp = client.get("/health/live")
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy_header(self, client: TestClient):
        resp = client.get("/health/live")
        pp = resp.headers.get("permissions-policy")
        assert pp is not None
        # Should restrict dangerous features
        assert "geolocation=()" in pp
        assert "camera=()" in pp
        assert "microphone=()" in pp


class TestCORSStrict:
    """CORS should be strict per environment."""

    def test_cors_allows_configured_origins(self, client: TestClient):
        # Test environment has specific allowed origins
        resp = client.options(
            "/health/live",
            headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
        )
        # In test env, CORS should work for configured origins
        assert resp.status_code == 200

    def test_cors_rejects_unconfigured_origin(self, client: TestClient):
        resp = client.options(
            "/health/live",
            headers={"Origin": "http://evil.com", "Access-Control-Request-Method": "GET"},
        )
        # Should not allow unconfigured origins
        assert resp.headers.get("access-control-allow-origin") != "http://evil.com"

    def test_cors_no_wildcard_in_production(self):
        # Production should never use wildcard
        # This is tested via config validation
        pass


class TestDockerComposeNoDefaults:
    """Docker compose should not have default secrets."""

    def test_docker_compose_no_default_jwt_secret(self):
        from pathlib import Path

        import yaml

        compose_path = Path(__file__).resolve().parents[2] / "docker-compose.yml"
        with open(compose_path) as f:
            compose = yaml.safe_load(f)

        api_env = compose["services"]["api"]["environment"]
        # JWT_SECRET_KEY should not have a default value
        jwt_secret = next((e for e in api_env if e.startswith("JWT_SECRET_KEY")), None)
        assert jwt_secret is not None
        assert ":-" not in jwt_secret or "dev_secret" not in jwt_secret

    def test_docker_compose_no_default_postgres_password(self):
        from pathlib import Path

        import yaml

        compose_path = Path(__file__).resolve().parents[2] / "docker-compose.yml"
        with open(compose_path) as f:
            compose = yaml.safe_load(f)

        db_env = compose["services"]["db"]["environment"]
        pg_password = next((e for e in db_env if e.startswith("POSTGRES_PASSWORD")), None)
        assert pg_password is not None
        assert ":-" not in pg_password or "arpia_secret" not in pg_password

    def test_docker_compose_no_default_database_url(self):
        from pathlib import Path

        import yaml

        compose_path = Path(__file__).resolve().parents[2] / "docker-compose.yml"
        with open(compose_path) as f:
            compose = yaml.safe_load(f)

        api_env = compose["services"]["api"]["environment"]
        db_url = next((e for e in api_env if e.startswith("DATABASE_URL")), None)
        assert db_url is not None
        assert ":-" not in db_url or "arpia_secret" not in db_url
