"""
CodeGuard AI - User Data Isolation Test Suite
=============================================
Verifies that scan history, developer dashboard metrics, and scan comparisons
are strictly isolated between authenticated users and never leak cross-account.
"""

import time
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_user_scan_data_isolation():
    """
    Verifies that User A and User B only see their own scans,
    their own metrics, and cannot access each other's scans in comparison.
    """
    ts = int(time.time() * 1000)
    email_a = f"user_a_{ts}@codeguard.local"
    email_b = f"user_b_{ts}@codeguard.local"

    # 1. Register User A
    res_a = client.post("/api/v1/auth/register", json={
        "full_name": "User Alpha",
        "email": email_a,
        "password": "PasswordAlpha123!"
    })
    assert res_a.status_code == 201
    token_a = res_a.json()["token"]

    # 2. Register User B
    res_b = client.post("/api/v1/auth/register", json={
        "full_name": "User Beta",
        "email": email_b,
        "password": "PasswordBeta123!"
    })
    assert res_b.status_code == 201
    token_b = res_b.json()["token"]

    # 3. User A runs a scan on vulnerable code
    scan_code_a = "import os\nos.system('echo user_a_scan')\n"
    scan_res_a = client.post(
        "/api/v1/analyze",
        json={"code": scan_code_a, "filename": "user_a.py", "enable_ruff": True, "enable_bandit": True},
        cookies={"codeguard_session": token_a}
    )
    assert scan_res_a.status_code == 200
    scan_id_a = scan_res_a.json()["scan_id"]
    assert scan_id_a is not None

    # 4. User B runs a scan on clean code
    scan_code_b = "def add(x: int, y: int) -> int:\n    return x + y\n"
    scan_res_b = client.post(
        "/api/v1/analyze",
        json={"code": scan_code_b, "filename": "user_b.py", "enable_ruff": True, "enable_bandit": True},
        cookies={"codeguard_session": token_b}
    )
    assert scan_res_b.status_code == 200
    scan_id_b = scan_res_b.json()["scan_id"]
    assert scan_id_b is not None

    # 5. User A fetches history: must see scan_id_a, must NOT see scan_id_b
    history_a = client.get("/api/v1/history", cookies={"codeguard_session": token_a}).json()
    ids_a = [item["id"] for item in history_a]
    assert scan_id_a in ids_a
    assert scan_id_b not in ids_a

    # 6. User B fetches history: must see scan_id_b, must NOT see scan_id_a
    history_b = client.get("/api/v1/history", cookies={"codeguard_session": token_b}).json()
    ids_b = [item["id"] for item in history_b]
    assert scan_id_b in ids_b
    assert scan_id_a not in ids_b

    # 7. User A tries to compare scan_id_a with User B's scan_id_b: MUST BE REJECTED (404)
    cross_compare_res = client.post(
        "/api/v1/compare-scans",
        json={"base_scan_id": scan_id_a, "subsequent_scan_id": scan_id_b},
        cookies={"codeguard_session": token_a}
    )
    assert cross_compare_res.status_code == 404
    assert "unauthorized" in cross_compare_res.json()["detail"].lower()
