"""
Unit and Integration Tests for CodeGuard AI API Endpoints
"""

from fastapi.testclient import TestClient
from app.main import app
from app.database.session import init_db

# Initialize database schema for tests
init_db()
client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "CodeGuard AI"


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "tools" in data


def test_security_headers_present():
    response = client.get("/")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in response.headers
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_samples_endpoint():
    response = client.get("/api/v1/samples")
    assert response.status_code == 200
    data = response.json()
    assert "vulnerable" in data
    assert "clean" in data


def test_metrics_endpoint():
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_scans" in data
    assert "average_health_score" in data
    assert "grade_distribution" in data
    assert "recent_scans" in data


def test_settings_endpoint():
    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    data = response.json()
    assert "ruff_available" in data
    assert "bandit_available" in data
    assert "max_code_size_kb" in data
    assert "timeout_seconds" in data
    assert "rate_limit_requests" in data
    assert "cors_origins" in data


def test_analyze_empty_code():
    response = client.post("/api/v1/analyze", json={"code": ""})
    assert response.status_code == 422


def test_analyze_whitespace_code():
    response = client.post("/api/v1/analyze", json={"code": "   \n\t  "})
    assert response.status_code == 422


def test_analyze_code_exceeding_limit():
    large_code = "a = 1\n" * 25000  # More than 100 KB
    response = client.post("/api/v1/analyze", json={"code": large_code})
    assert response.status_code == 413


def test_analyze_valid_vulnerable_code():
    code = (
        "import os\n"
        "DATABASE_KEY = 'secret_12345'\n"
        "def run_query(q):\n"
        "    query = f'SELECT * FROM users WHERE name = {q}'\n"
        "    assert q != ''\n"
    )
    response = client.post(
        "/api/v1/analyze",
        json={"code": code, "filename": "sample.py", "enable_ruff": True, "enable_bandit": True}
    )
    assert response.status_code == 200
    data = response.json()

    assert "summary" in data
    assert "findings" in data
    assert "scanners" in data
    assert len(data["scanners"]) == 2
    assert data["summary"]["total_findings"] > 0
    assert data["summary"]["health_score"] < 100
    assert data["scan_id"] is not None
    assert "disclaimer" in data

    # Verify telemetry
    scanner_names = [s["name"] for s in data["scanners"]]
    assert "ruff" in scanner_names
    assert "bandit" in scanner_names


def test_analyze_selective_tools():
    code = "import os\n"
    # Disable bandit, only run ruff
    response = client.post(
        "/api/v1/analyze",
        json={"code": code, "enable_ruff": True, "enable_bandit": False}
    )
    assert response.status_code == 200
    data = response.json()
    bandit_telemetry = next(s for s in data["scanners"] if s["name"] == "bandit")
    assert bandit_telemetry["status"] == "disabled"


def test_history_endpoint():
    response = client.get("/api/v1/history?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_explain_finding_endpoint():
    response = client.post(
        "/api/v1/explain-finding",
        json={"rule_id": "B608", "message": "Possible SQL injection", "code_snippet": "query = 'SELECT ' + q"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rule_id"] == "B608"
    assert "explanation" in data
    assert "disclaimer" in data

