"""Login attempt tracking and lockout mechanism."""
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import ClassVar


@dataclass
class LoginAttemptTracker:
    """Track failed login attempts and enforce lockout.

    Uses in-memory storage with process lifetime. For production deployment
    with multiple workers, replace with Redis-backed implementation.
    """

    # Configuration
    max_attempts: int = 5
    lockout_duration_seconds: int = 900  # 15 minutes
    window_seconds: int = 900  # 15 minute sliding window

    # In-memory storage: key -> list of attempt timestamps
    _attempts: ClassVar[dict[str, list[float]]] = defaultdict(list)
    _lock: ClassVar[Lock] = Lock()

    @classmethod
    def _make_key(cls, email: str, ip: str) -> str:
        """Create tracking key from email and IP."""
        return f"{email.lower()}:{ip}"

    @classmethod
    def _cleanup_old_attempts(cls, key: str, now: float) -> None:
        """Remove attempts outside the sliding window."""
        cutoff = now - cls.window_seconds
        cls._attempts[key] = [ts for ts in cls._attempts[key] if ts > cutoff]
        if not cls._attempts[key]:
            del cls._attempts[key]

    @classmethod
    def record_failure(cls, email: str, ip: str) -> int:
        """Record a failed login attempt. Returns current attempt count."""
        key = cls._make_key(email, ip)
        now = time.time()

        with cls._lock:
            cls._cleanup_old_attempts(key, now)
            cls._attempts[key].append(now)
            return len(cls._attempts[key])

    @classmethod
    def is_locked_out(cls, email: str, ip: str) -> tuple[bool, int]:
        """Check if the email/IP is locked out. Returns (locked_out, remaining_seconds)."""
        key = cls._make_key(email, ip)
        now = time.time()

        with cls._lock:
            cls._cleanup_old_attempts(key, now)
            attempts = cls._attempts.get(key, [])

            if len(attempts) >= cls.max_attempts:
                # Locked out - calculate remaining time
                oldest_in_window = attempts[0]
                lockout_expires = oldest_in_window + cls.lockout_duration_seconds
                remaining = int(lockout_expires - now)
                if remaining > 0:
                    return True, remaining
                else:
                    # Lockout expired, clear attempts
                    del cls._attempts[key]
                    return False, 0

            return False, 0

    @classmethod
    def record_success(cls, email: str, ip: str) -> None:
        """Record successful login - clear failed attempts."""
        key = cls._make_key(email, ip)
        with cls._lock:
            if key in cls._attempts:
                del cls._attempts[key]

    @classmethod
    def reset(cls) -> None:
        """Reset all tracking (for testing)."""
        with cls._lock:
            cls._attempts.clear()