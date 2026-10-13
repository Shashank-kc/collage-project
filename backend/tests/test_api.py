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


def test_samples_endpoint():
    response = client.get("/api/v1/samples")
    assert response.status_code == 200
    data = response.json()
    assert "vulnerable" in data
    assert "clean" in data


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
    response = client.post("/api/v1/analyze", json={"code": code, "filename": "sample.py"})
    assert response.status_code == 200
    data = response.json()

    assert "summary" in data
    assert "findings" in data
    assert data["summary"]["total_findings"] > 0
    assert data["summary"]["health_score"] < 100
    assert data["scan_id"] is not None
    assert "disclaimer" in data


def test_history_endpoint():
    response = client.get("/api/v1/history?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
