from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Rate limiting is a runtime protection; the test suite (ENVIRONMENT=test)
# performs many logins from the same TestClient IP and would trip the limit.
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.ENVIRONMENT != "test",
)
