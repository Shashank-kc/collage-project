"""
CodeGuard AI - AI Assistant & Conversation Isolation Test Suite
===============================================================
Tests AI Assistant status, conversation CRUD, per-user chat history isolation,
input validation, error handling, finding context integration, and mock OpenAI responses.
"""

import time
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.openai_service import openai_service

client = TestClient(app)


def test_assistant_status_unauthenticated():
    """Verifies that status check is public and never leaks the API key."""
    res = client.get("/api/v1/assistant/status")
    assert res.status_code == 200
    data = res.json()
    assert "available" in data
    assert "model" in data
    assert "api_key" not in data
    assert "key" not in data


def test_assistant_protected_endpoints():
    """Verifies unauthenticated requests to chat and conversations return 401."""
    chat_res = client.post("/api/v1/assistant/chat", json={"message": "Hello"})
    assert chat_res.status_code == 401

    conv_res = client.get("/api/v1/assistant/conversations")
    assert conv_res.status_code == 401


def test_conversation_crud_and_isolation():
    """Verifies user can create, list, view, and delete their own conversations, and cannot access others'."""
    ts = int(time.time() * 1000)
    email_a = f"ai_user_a_{ts}@codeguard.local"
    email_b = f"ai_user_b_{ts}@codeguard.local"

    # Register user A
    res_a = client.post("/api/v1/auth/register", json={
        "full_name": "AI User A",
        "email": email_a,
        "password": "Password123!"
    })
    token_a = res_a.json()["token"]

    # Register user B
    res_b = client.post("/api/v1/auth/register", json={
        "full_name": "AI User B",
        "email": email_b,
        "password": "Password123!"
    })
    token_b = res_b.json()["token"]

    # 1. User A creates a conversation
    create_res = client.post(
        "/api/v1/assistant/conversations?title=SQL%20Injection%20Review",
        cookies={"codeguard_session": token_a}
    )
    assert create_res.status_code == 201
    conv_a_id = create_res.json()["id"]

    # 2. User A lists conversations: must see conv_a_id
    list_a = client.get("/api/v1/assistant/conversations", cookies={"codeguard_session": token_a}).json()
    assert any(c["id"] == conv_a_id for c in list_a)

    # 3. User B lists conversations: must NOT see conv_a_id
    list_b = client.get("/api/v1/assistant/conversations", cookies={"codeguard_session": token_b}).json()
    assert not any(c["id"] == conv_a_id for c in list_b)

    # 4. User B tries to get User A's conversation: returns 404
    cross_get = client.get(
        f"/api/v1/assistant/conversations/{conv_a_id}",
        cookies={"codeguard_session": token_b}
    )
    assert cross_get.status_code == 404

    # 5. User B tries to delete User A's conversation: returns 404
    cross_del = client.delete(
        f"/api/v1/assistant/conversations/{conv_a_id}",
        cookies={"codeguard_session": token_b}
    )
    assert cross_del.status_code == 404

    # 6. User A deletes their own conversation: returns 200
    del_res = client.delete(
        f"/api/v1/assistant/conversations/{conv_a_id}",
        cookies={"codeguard_session": token_a}
    )
    assert del_res.status_code == 200


def test_chat_with_mocked_openai_response():
    """Verifies sending a message with finding context and receiving an AI response."""
    ts = int(time.time() * 1000)
    email = f"chat_user_{ts}@codeguard.local"

    res = client.post("/api/v1/auth/register", json={
        "full_name": "Chat Reviewer",
        "email": email,
        "password": "Password123!"
    })
    token = res.json()["token"]

    mock_ai_reply = (
        "### Finding Analysis: B608 (SQL Injection)\n\n"
        "The string concatenation allows an attacker to manipulate SQL syntax.\n\n"
        "```python\n"
        "# Recommended remediation:\n"
        "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))\n"
        "```\n\n"
        "Remember to run a subsequent scan to verify the fix."
    )

    with patch.object(openai_service, "generate_chat_response", return_value=mock_ai_reply):
        chat_res = client.post(
            "/api/v1/assistant/chat",
            json={
                "message": "How do I fix this SQL injection issue?",
                "finding_context": {
                    "rule_id": "B608",
                    "tool": "bandit",
                    "severity": "HIGH",
                    "message": "Possible SQL injection vector through string-based query construction.",
                    "line": 42,
                    "code_snippet": "query = f'SELECT * FROM users WHERE id = {user_id}'"
                },
                "include_code": True
            },
            cookies={"codeguard_session": token}
        )
        assert chat_res.status_code == 200
        data = chat_res.json()
        assert data["sender"] == "assistant"
        assert "B608" in data["content"]
        assert data["is_ai"] is True
        assert data["conversation_id"] is not None

        # Verify conversation history persisted both user and assistant messages
        conv_id = data["conversation_id"]
        history_res = client.get(
            f"/api/v1/assistant/conversations/{conv_id}",
            cookies={"codeguard_session": token}
        )
        assert history_res.status_code == 200
        msgs = history_res.json()["messages"]
        assert len(msgs) == 2
        assert msgs[0]["sender"] == "user"
        assert msgs[1]["sender"] == "assistant"


def test_chat_unconfigured_openai_key():
    """Verifies that missing OPENAI_API_KEY gracefully returns 503 without crashing the server."""
    ts = int(time.time() * 1000)
    email = f"no_key_user_{ts}@codeguard.local"

    res = client.post("/api/v1/auth/register", json={
        "full_name": "No Key Tester",
        "email": email,
        "password": "Password123!"
    })
    token = res.json()["token"]

    # Temporarily force is_configured to False
    with patch.object(type(openai_service), "is_configured", False):
        chat_res = client.post(
            "/api/v1/assistant/chat",
            json={"message": "Can you explain this vulnerability?"},
            cookies={"codeguard_session": token}
        )
        assert chat_res.status_code == 503
        assert "OPENAI_API_KEY is not configured" in chat_res.json()["detail"]


def test_chat_input_validation_empty_and_oversized():
    """Verifies that empty or whitespace-only prompts and oversized inputs are rejected."""
    ts = int(time.time() * 1000)
    email = f"val_user_{ts}@codeguard.local"

    res = client.post("/api/v1/auth/register", json={
        "full_name": "Validation Tester",
        "email": email,
        "password": "Password123!"
    })
    token = res.json()["token"]

    # 1. Empty message
    empty_res = client.post(
        "/api/v1/assistant/chat",
        json={"message": "   "},
        cookies={"codeguard_session": token}
    )
    assert empty_res.status_code == 422

    # 2. Oversized message (> 10000 characters)
    huge_message = "A" * 10001
    huge_res = client.post(
        "/api/v1/assistant/chat",
        json={"message": huge_message},
        cookies={"codeguard_session": token}
    )
    assert huge_res.status_code == 422


def test_chat_error_handling_quota_and_timeout():
    """Verifies that OpenAI rate-limit, quota, and timeout errors map to appropriate HTTP status codes."""
    ts = int(time.time() * 1000)
    email = f"err_user_{ts}@codeguard.local"

    res = client.post("/api/v1/auth/register", json={
        "full_name": "Error Tester",
        "email": email,
        "password": "Password123!"
    })
    token = res.json()["token"]

    # Test quota/rate limit error mapping to 429
    with patch.object(openai_service, "generate_chat_response", side_effect=ValueError("OpenAI rate limit or usage quota exceeded.")):
        res_429 = client.post(
            "/api/v1/assistant/chat",
            json={"message": "Explain B608"},
            cookies={"codeguard_session": token}
        )
        assert res_429.status_code == 429
        assert "rate limit" in res_429.json()["detail"].lower()

    # Test timeout error mapping to 502
    with patch.object(openai_service, "generate_chat_response", side_effect=ValueError("The request to OpenAI timed out after 30 seconds.")):
        res_502 = client.post(
            "/api/v1/assistant/chat",
            json={"message": "Explain B608"},
            cookies={"codeguard_session": token}
        )
        assert res_502.status_code == 502
        assert "timed out" in res_502.json()["detail"].lower()


def test_assistant_per_user_rate_limiting():
    """Verifies that exceeding per-user AI rate limit triggers HTTP 429."""
    from app.api.assistant_routes import check_ai_rate_limit
    from fastapi import HTTPException

    test_user_id = 9999
    # First 10 requests pass
    for _ in range(10):
        check_ai_rate_limit(test_user_id)

    # 11th request triggers 429
    with pytest.raises(HTTPException) as exc_info:
        check_ai_rate_limit(test_user_id)

    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail
