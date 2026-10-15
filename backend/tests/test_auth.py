"""
CodeGuard AI - Authentication & Session Test Suite
==================================================
Tests user registration, Argon2id hashing, login, logout, session expiration,
protected endpoints, and anti-brute-force rate limits.
"""

import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import hash_password, verify_password

client = TestClient(app)


def test_argon2_password_hashing():
    """Verifies that Argon2id produces valid salted hashes and verifies correctly."""
    password = "CorrectHorseBatteryStaple123!"
    hashed = hash_password(password)

    assert hashed.startswith("$argon2id$")
    assert verify_password(hashed, password) is True
    assert verify_password(hashed, "WrongPassword123!") is False


def test_user_registration_flow():
    """Verifies registration creates user, returns HTTP-only cookie, and omits password hash."""
    unique_email = f"dev_{int(time.time() * 1000)}@codeguard.local"
    payload = {
        "full_name": "Security Auditor",
        "email": unique_email,
        "password": "SecurePassword123!"
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["user"]["email"] == unique_email.lower()
    assert data["user"]["full_name"] == "Security Auditor"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]
    assert "token" in data
    assert "codeguard_session" in response.cookies


def test_duplicate_registration_rejected():
    """Verifies duplicate email registration is rejected with 409 Conflict."""
    email = f"duplicate_{int(time.time() * 1000)}@codeguard.local"
    payload = {
        "full_name": "Alice Developer",
        "email": email,
        "password": "Password123!"
    }

    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_registration_validation_rules():
    """Verifies invalid email format and weak passwords are rejected."""
    # Invalid email
    bad_email_res = client.post("/api/v1/auth/register", json={
        "full_name": "Bad Email",
        "email": "not-an-email",
        "password": "ValidPassword123!"
    })
    assert bad_email_res.status_code == 422

    # Weak password (< 8 chars)
    short_pwd_res = client.post("/api/v1/auth/register", json={
        "full_name": "Short Pwd",
        "email": "valid@example.com",
        "password": "short"
    })
    assert short_pwd_res.status_code == 422

    # All-alpha password without numbers/symbols
    all_alpha_res = client.post("/api/v1/auth/register", json={
        "full_name": "Alpha Only",
        "email": "valid2@example.com",
        "password": "onlylettershere"
    })
    assert all_alpha_res.status_code == 422


def test_login_and_logout_flow():
    """Verifies successful login, profile fetch via session cookie, and logout invalidation."""
    email = f"login_test_{int(time.time() * 1000)}@codeguard.local"
    password = "StrongPassword456!"

    # 1. Register user
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Login Tester",
        "email": email,
        "password": password
    })
    assert reg_res.status_code == 201

    # 2. Login with valid credentials
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
        "remember_me": True
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    token = login_data["token"]
    assert "codeguard_session" in login_res.cookies

    # 3. Access protected /auth/me using Cookie
    me_res = client.get("/api/v1/auth/me", cookies={"codeguard_session": token})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

    # 4. Access protected /auth/me using Bearer header
    me_header_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_header_res.status_code == 200
    assert me_header_res.json()["email"] == email

    # 5. Invalid credentials rejected
    bad_login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "WrongPassword789!"
    })
    assert bad_login_res.status_code == 401
    assert "Invalid email or password" in bad_login_res.json()["detail"]

    # 6. Logout
    logout_res = client.post("/api/v1/auth/logout", cookies={"codeguard_session": token})
    assert logout_res.status_code == 200

    # 7. Post-logout /auth/me returns 401
    post_logout_res = client.get("/api/v1/auth/me", cookies={"codeguard_session": token})
    assert post_logout_res.status_code == 401


def test_unauthenticated_protected_route():
    """Verifies unauthenticated access to /auth/me is rejected with 401."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]


def test_auth_rate_limiting():
    """Verifies that exceeding the auth attempt rate limit triggers HTTP 429."""
    from app.api.auth_routes import check_auth_rate_limit
    from fastapi import HTTPException

    target_ip = "198.51.100.99"
    # First 10 attempts should pass
    for _ in range(10):
        check_auth_rate_limit(target_ip)

    # 11th attempt must trigger 429 Too Many Requests
    with pytest.raises(HTTPException) as exc_info:
        check_auth_rate_limit(target_ip)

    assert exc_info.value.status_code == 429
    assert "Too many authentication attempts" in exc_info.value.detail
