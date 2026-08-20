"""Password policy validation and TOTP MFA utilities."""
import re
import secrets
from typing import Optional

import pyotp


class PasswordPolicyError(ValueError):
    """Raised when password doesn't meet policy requirements."""

    pass


def validate_password_strength(password: str) -> None:
    """Validate password meets strength requirements.

    Requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - No common patterns (sequential, repeated)
    """
    errors = []

    if len(password) < 12:
        errors.append("La contraseña debe tener al menos 12 caracteres")

    if not re.search(r"[A-Z]", password):
        errors.append("La contraseña debe contener al menos una letra mayúscula")

    if not re.search(r"[a-z]", password):
        errors.append("La contraseña debe contener al menos una letra minúscula")

    if not re.search(r"\d", password):
        errors.append("La contraseña debe contener al menos un dígito")

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        errors.append("La contraseña debe contener al menos un carácter especial")

    # Check for common patterns
    # Sequential characters (abc, 123, etc.) - only flag longer sequences (4+ chars)
    if re.search(r"(?:abcd|bcde|cdef|defg|efgh|fghi|ghij|hijk|ijkl|jklm|klmn|lmno|mnop|nopq|opqr|pqrs|qrst|rstu|stuv|tuvw|uvwx|vwxy|wxyz|0123|1234|2345|3456|4567|5678|6789)", password.lower()):
        errors.append("La contraseña no debe contener secuencias de 4+ caracteres consecutivos")

    # Repeated characters (aaaa, 1111, etc.) - only flag 4+ same chars
    if re.search(r"(.)\1{3,}", password):
        errors.append("La contraseña no debe contener el mismo carácter repetido 4+ veces seguidas")

    # Common passwords
    common_passwords = [
        "password", "admin123", "qwerty", "letmein", "welcome",
        "monkey", "dragon", "master", "shadow", "superman",
    ]
    if password.lower() in common_passwords:
        errors.append("La contraseña es demasiado común")

    if errors:
        raise PasswordPolicyError("; ".join(errors))


def generate_totp_secret() -> str:
    """Generate a new TOTP secret (base32 encoded)."""
    return pyotp.random_base32()


def verify_totp(secret: str, code: str, valid_window: int = 1) -> bool:
    """Verify a TOTP code against the secret.

    Args:
        secret: Base32 encoded TOTP secret
        code: 6-digit TOTP code from authenticator app
        valid_window: Number of time steps (30s each) to accept around current time
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=valid_window)


def get_totp_uri(secret: str, email: str, issuer: str = "ERP Arpia") -> str:
    """Generate otpauth:// URI for QR code."""
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def hash_password(password: str) -> str:
    """Hash password using bcrypt (re-export from security for convenience)."""
    from app.core.security import hash_password as _hash_password
    return _hash_password(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify password against hash (re-export from security for convenience)."""
    from app.core.security import verify_password as _verify_password
    return _verify_password(plain_password, password_hash)