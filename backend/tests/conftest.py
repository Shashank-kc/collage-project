"""
CodeGuard AI - PyTest Configuration and Fixtures
================================================
Resets in-memory rate-limiter buckets between tests so tests run reliably.
"""

import os
import pytest

# Flag test execution environment
os.environ["TESTING"] = "true"

from app.api.auth_routes import _auth_attempt_history
from app.api.assistant_routes import _ai_user_request_history


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Cleans in-memory rate limiting state before and after each test."""
    _auth_attempt_history.clear()
    _ai_user_request_history.clear()
    yield
    _auth_attempt_history.clear()
    _ai_user_request_history.clear()
