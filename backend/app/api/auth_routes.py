"""
CodeGuard AI - Authentication API Endpoints
===========================================
Handles user registration, login with Argon2id password verification,
session lifecycle (cookie-based & Bearer fallback), current user queries,
and anti-brute-force rate limiting.
"""

from collections import defaultdict
import time
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.config import (
    AUTH_RATE_LIMIT_REQUESTS,
    AUTH_RATE_LIMIT_WINDOW_SECONDS,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SECURE,
)
from app.database.session import create_user, get_user_by_email
from app.schemas.auth import (
    AuthSuccessResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import (
    create_user_session,
    get_current_user,
    get_session_token_from_request,
    hash_password,
    invalidate_user_session,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# In-memory sliding-window rate limiter for sensitive authentication endpoints
_auth_attempt_history: dict[str, list[float]] = defaultdict(list)


def check_auth_rate_limit(client_ip: str) -> None:
    """Enforces rate limits on authentication requests to prevent credential stuffing."""
    now = time.time()
    cutoff = now - AUTH_RATE_LIMIT_WINDOW_SECONDS

    # Clean old records
    attempts = [t for t in _auth_attempt_history[client_ip] if t > cutoff]
    attempts.append(now)
    _auth_attempt_history[client_ip] = attempts

    if len(attempts) > AUTH_RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please wait a minute before trying again."
        )


def set_auth_cookie(response: Response, token: str, max_age: int) -> None:
    """Configures secure HTTP-only session cookie on the response."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        expires=max_age,
        path="/",
        httponly=True,
        samesite="lax",
        secure=SESSION_COOKIE_SECURE
    )


@router.post("/register", response_model=AuthSuccessResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest, request: Request, response: Response):
    """
    Registers a new developer account using Argon2id password hashing.
    Issues a secure HTTP-only session upon successful creation.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    check_auth_rate_limit(client_ip)

    # Check for existing email address
    existing_user = get_user_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please sign in instead."
        )

    # Hash password with Argon2id
    pwd_hash = hash_password(payload.password)

    # Store user in database
    created = create_user(
        email=payload.email,
        password_hash=pwd_hash,
        full_name=payload.full_name
    )

    # Create active session
    token, _, max_age = create_user_session(user_id=created["id"], remember_me=False)
    set_auth_cookie(response, token, max_age)

    return AuthSuccessResponse(
        user=UserResponse(
            id=created["id"],
            email=created["email"],
            full_name=created["full_name"],
            created_at=created["created_at"]
        ),
        message="Account created successfully.",
        token=token
    )


@router.post("/login", response_model=AuthSuccessResponse)
async def login(payload: UserLoginRequest, request: Request, response: Response):
    """
    Authenticates account credentials against stored Argon2id hash.
    On success, creates a session and returns secure HTTP-only cookie.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    check_auth_rate_limit(client_ip)

    user_data = get_user_by_email(payload.email)
    if not user_data:
        # Uniform rejection message prevents account enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )

    if not verify_password(user_data["password_hash"], payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )

    # Create session
    token, _, max_age = create_user_session(
        user_id=user_data["id"],
        remember_me=payload.remember_me
    )
    set_auth_cookie(response, token, max_age)

    return AuthSuccessResponse(
        user=UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            created_at=user_data["created_at"]
        ),
        message="Sign in successful.",
        token=token
    )


@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Terminates the current session, removes the record from SQLite,
    and clears the HTTP-only cookie.
    """
    token = get_session_token_from_request(request)
    if token:
        invalidate_user_session(token)

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        samesite="lax"
    )

    return {"message": "Signed out successfully."}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: UserResponse = Depends(get_current_user)):
    """
    Protected endpoint: returns the authenticated user's profile.
    Rejects unauthorized access with HTTP 401.
    """
    return user
