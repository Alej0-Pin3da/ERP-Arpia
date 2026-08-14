import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_development_allows_default_secret():
    s = Settings(ENVIRONMENT="development", JWT_SECRET_KEY="dev_secret_change_me")
    assert s.JWT_SECRET_KEY == "dev_secret_change_me"


def test_settings_production_rejects_default_secret():
    with pytest.raises(ValidationError) as excinfo:
        Settings(ENVIRONMENT="production", JWT_SECRET_KEY="dev_secret_change_me")
    assert "JWT_SECRET_KEY must be configured with a secure secret" in str(excinfo.value)


def test_settings_production_accepts_secure_secret():
    s = Settings(
        ENVIRONMENT="production", JWT_SECRET_KEY="super_secure_production_secret_key_12345"
    )
    assert s.JWT_SECRET_KEY == "super_secure_production_secret_key_12345"


def test_cors_origins_list():
    s = Settings(CORS_ORIGINS="http://localhost:5173, https://arpia.com.co")
    assert s.cors_origins_list == ["http://localhost:5173", "https://arpia.com.co"]
