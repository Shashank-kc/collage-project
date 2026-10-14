"""
Unit Tests for Security Controls, Health Score, and Sandboxing
"""

import os
from pathlib import Path
import tempfile
from fastapi.testclient import TestClient
from app.main import app
from app.services.coordinator import AnalysisCoordinator
from app.config import MAX_CODE_SIZE_BYTES

client = TestClient(app)


def test_health_score_calculation_logic():
    coordinator = AnalysisCoordinator()

    # 1. Zero issues -> 100, Grade A
    score, grade = coordinator._calculate_health_score(0, 0, 0, 0, 0)
    assert score == 100
    assert grade == "A"

    # 2. 1 Low issue (-3 pts) -> 97, Grade A
    score, grade = coordinator._calculate_health_score(0, 0, 0, 1, 0)
    assert score == 97
    assert grade == "A"

    # 3. 1 High issue (-15 pts) -> 85, Grade B
    score, grade = coordinator._calculate_health_score(0, 1, 0, 0, 0)
    assert score == 85
    assert grade == "B"

    # 4. 1 Critical (-25 pts) + 1 High (-15 pts) -> 60, Grade D
    score, grade = coordinator._calculate_health_score(1, 1, 0, 0, 0)
    assert score == 60
    assert grade == "D"

    # 5. Severe multiple vulnerabilities clamped at 0, Grade F
    score, grade = coordinator._calculate_health_score(5, 5, 5, 5, 5)
    assert score == 0
    assert grade == "F"


def test_temp_file_sandboxing_and_cleanup():
    coordinator = AnalysisCoordinator()
    sample_code = "x = 42\n"

    # Count existing codeguard temp dirs in system tempdir
    temp_root = Path(tempfile.gettempdir())
    initial_dirs = list(temp_root.glob("codeguard_*"))

    # Execute analysis
    coordinator.run_analysis(sample_code)

    # After run_analysis exits, its temporary directory must be completely cleaned up
    remaining_dirs = list(temp_root.glob("codeguard_*"))
    assert len(remaining_dirs) <= len(initial_dirs)


def test_oversized_payload_rejection():
    # Exactly 1 byte beyond max limit
    huge_code = "x = 1\n" * ((MAX_CODE_SIZE_BYTES // 6) + 10)
    response = client.post("/api/v1/analyze", json={"code": huge_code})
    assert response.status_code == 413
    assert "exceeds maximum limit" in response.json()["detail"]


def test_rate_limiting_enforcement():
    # Create an app instance with a low threshold to test rate limiting without flooding
    from app.middleware.security import RateLimitingMiddleware
    from fastapi import FastAPI

    test_app = FastAPI()
    test_app.add_middleware(RateLimitingMiddleware, max_requests=3, window_seconds=10)

    @test_app.get("/test")
    def ping():
        return {"msg": "ok"}

    test_client = TestClient(test_app)

    # Requests 1, 2, 3 must succeed
    r1 = test_client.get("/test")
    assert r1.status_code == 200
    assert r1.headers.get("X-RateLimit-Remaining") == "2"

    r2 = test_client.get("/test")
    assert r2.status_code == 200
    assert r2.headers.get("X-RateLimit-Remaining") == "1"

    r3 = test_client.get("/test")
    assert r3.status_code == 200
    assert r3.headers.get("X-RateLimit-Remaining") == "0"

    # Request 4 must trigger 429 Too Many Requests
    r4 = test_client.get("/test")
    assert r4.status_code == 429
    assert "Retry-After" in r4.headers
    assert "Rate limit exceeded" in r4.json()["detail"]
