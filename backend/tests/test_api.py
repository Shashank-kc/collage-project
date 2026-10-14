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


def test_finding_structured_explain_fix_verify_fields():
    code = "assert x == 1, 'error'\n"
    response = client.post(
        "/api/v1/analyze",
        json={"code": code, "filename": "test_assert.py", "enable_ruff": True, "enable_bandit": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["findings"]) > 0
    b101_finding = next((f for f in data["findings"] if f["rule_id"] == "B101"), None)
    if b101_finding:
        assert b101_finding["what_detected"] is not None
        assert b101_finding["why_it_matters"] is not None
        assert b101_finding["where_is_it"] is not None
        assert b101_finding["how_to_improve"] is not None
        assert b101_finding["safer_example"] is not None
        assert b101_finding["verification_guide"] is not None


def test_verify_fix_resolved():
    # Initial vulnerable code with assert
    # Updated code replaces assert with explicit exception
    updated_code = (
        "def check_token(token):\n"
        "    if not token:\n"
        "        raise ValueError('Token is required')\n"
        "    return token\n"
    )
    response = client.post(
        "/api/v1/verify-fix",
        json={
            "original_rule_id": "B101",
            "prior_score": 75,
            "prior_finding_count": 1,
            "updated_code": updated_code,
            "enable_ruff": True,
            "enable_bandit": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RESOLVED"
    assert data["rule_id"] == "B101"
    assert data["new_score"] >= data["prior_score"]
    assert "subsequent_analysis" in data


def test_verify_fix_still_detected():
    # Code still contains the assert flaw
    still_vulnerable_code = "assert 1 == 1\n"
    response = client.post(
        "/api/v1/verify-fix",
        json={
            "original_rule_id": "B101",
            "prior_score": 75,
            "prior_finding_count": 1,
            "updated_code": still_vulnerable_code,
            "enable_ruff": False,
            "enable_bandit": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "STILL_DETECTED"
    assert "still detected" in data["message"].lower()


def test_compare_scans_endpoint():
    # Submit first scan
    res1 = client.post("/api/v1/analyze", json={"code": "import os\nimport sys\n", "filename": "s1.py"})
    scan1_id = res1.json()["scan_id"]

    # Submit second scan
    res2 = client.post("/api/v1/analyze", json={"code": "import os\n", "filename": "s2.py"})
    scan2_id = res2.json()["scan_id"]

    response = client.post(
        "/api/v1/compare-scans",
        json={"base_scan_id": scan1_id, "subsequent_scan_id": scan2_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert "resolved_count" in data
    assert "remaining_count" in data
    assert "score_delta" in data


