"""
CodeGuard AI - Authentication Service (Argon2id & Secure Sessions)
==================================================================
Manages password hashing with Argon2id, cryptographically secure session
tokens, and FastAPI dependency injection for protected endpoints.
"""

from datetime import datetime, timedelta, timezone
import logging
import secrets
from typing import Optional, Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash
from fastapi import HTTPException, Request, status

from app.config import (
    SESSION_COOKIE_NAME,
    SESSION_EXPIRE_DAYS,
)
from app.database.session import (
    create_session,
    create_user,
    delete_session,
    get_session_user,
    get_user_by_email,
)
from app.schemas.auth import UserResponse

logger = logging.getLogger(__name__)

# Argon2id password hasher with secure default parameters
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16
)


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id with unique salt."""
    return _hasher.hash(password)


def verify_password(password_hash: str, candidate_password: str) -> bool:
    """Safely verifies a candidate password against an Argon2id hash."""
    try:
        return _hasher.verify(password_hash, candidate_password)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False
    except Exception as exc:
        logger.error("Unexpected error during password verification: %s", exc)
        return False


def create_user_session(user_id: int, remember_me: bool = False) -> Tuple[str, str, int]:
    """
    Generates a cryptographically strong session token and persists it in SQLite.
    Returns: (session_id, expires_at_iso, max_age_seconds)
    """
    session_id = secrets.token_urlsafe(32)
    # Default: 7 days; Remember-me: 30 days
    days = 30 if remember_me else SESSION_EXPIRE_DAYS
    expires_dt = datetime.now(timezone.utc) + timedelta(days=days)
    expires_iso = expires_dt.isoformat()
    max_age_seconds = days * 24 * 60 * 60

    create_session(session_id=session_id, user_id=user_id, expires_at=expires_iso)
    return session_id, expires_iso, max_age_seconds


def invalidate_user_session(session_id: str) -> None:
    """Destroys an active session in the database."""
    delete_session(session_id)


def get_session_token_from_request(request: Request) -> Optional[str]:
    """
    Extracts session token prioritizing HTTP-only cookie, with fallback
    to Authorization Bearer header for programmatic API clients and automated tests.
    """
    # 1. Cookie
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        return token

    # 2. Authorization Header fallback: Bearer <token>
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:].strip()
        if bearer_token:
            return bearer_token

    return None


async def get_current_user(request: Request) -> UserResponse:
    """
    FastAPI dependency: Enforces that the request comes from an authenticated user.
    Raises HTTP 401 if token is missing, invalid, or expired.
    """
    token = get_session_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to access this resource."
        )

    user_data = get_session_user(token)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please sign in again."
        )

    return UserResponse(
        id=user_data["id"],
        email=user_data["email"],
        full_name=user_data["full_name"],
        created_at=user_data["created_at"]
    )


async def get_optional_user(request: Request) -> Optional[UserResponse]:
    """
    FastAPI dependency: Resolves user identity if an active session exists,
    otherwise returns None without raising an exception.
    Enables backward compatibility while isolating data when logged in.
    """
    token = get_session_token_from_request(request)
    if not token:
        return None

    user_data = get_session_user(token)
    if not user_data:
        return None

    return UserResponse(
        id=user_data["id"],
        email=user_data["email"],
        full_name=user_data["full_name"],
        created_at=user_data["created_at"]
    )
