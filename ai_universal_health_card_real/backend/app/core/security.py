from datetime import datetime, timedelta, timezone
import hashlib
import secrets

import jwt
from passlib.context import CryptContext

from app.core.config import settings


# ============================================================
# PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Convert plain-text password into a secure bcrypt hash.
    """

    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    if not password:
        raise ValueError("Password cannot be empty")

    return pwd_context.hash(password)


def verify_password(
    password: str,
    password_hash: str
) -> bool:
    """
    Verify plain-text password against stored bcrypt hash.
    """

    if not isinstance(password, str):
        return False

    if not isinstance(password_hash, str):
        return False

    if not password:
        return False

    if not password_hash:
        return False

    try:
        return pwd_context.verify(
            password,
            password_hash
        )
    except Exception:
        return False


# ============================================================
# ACCESS TOKEN
# ============================================================

def create_access_token(
    user_id: int,
    role: str
) -> str:

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=settings.access_token_minutes
        )
    )

    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


# ============================================================
# REFRESH TOKEN
# ============================================================

def create_refresh_token(
    user_id: int
) -> str:

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            days=settings.refresh_token_days
        )
    )

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


# ============================================================
# DECODE JWT
# ============================================================

def decode_token(
    token: str
):
    """
    Decode and validate JWT token.
    """

    if not token:
        raise ValueError("Token is required")

    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )


# ============================================================
# RANDOM TOKEN
# ============================================================

def random_token() -> str:
    """
    Generate cryptographically secure random token.
    """

    return secrets.token_urlsafe(48)


# ============================================================
# TOKEN HASH
# ============================================================

def token_hash(
    token: str
) -> str:
    """
    SHA-256 hash for one-time tokens.
    """

    if not token:
        raise ValueError("Token cannot be empty")

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()