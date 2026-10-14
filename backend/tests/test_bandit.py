"""
Unit Tests for Bandit Security Analyzer Service
"""

import tempfile
from pathlib import Path
from app.services.bandit_analyzer import BanditAnalyzer
from app.schemas.analysis import FindingCategory


def test_bandit_detects_security_issues():
    analyzer = BanditAnalyzer()
    vulnerable_code = (
        "import hashlib\n"
        "def check():\n"
        "    assert 1 == 1\n"
        "    eval('1 + 1')\n"
        "    hashlib.md5(b'test').hexdigest()\n"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "test.py"
        temp_file.write_text(vulnerable_code, encoding="utf-8")

        findings, telemetry = analyzer.analyze(str(temp_file), vulnerable_code)

    assert len(findings) > 0
    rule_ids = [f.rule_id for f in findings]
    # B101 is assert_used, B307 is eval, B303/B324 is md5
    assert "B101" in rule_ids or "B307" in rule_ids
    assert all(f.category == FindingCategory.SECURITY for f in findings)
    assert telemetry.status == "completed"
    assert telemetry.findings_count > 0
    assert findings[0].why_it_matters is not None


def test_bandit_clean_code():
    analyzer = BanditAnalyzer()
    clean_code = "def safe_add(a: int, b: int) -> int:\n    return a + b\n"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "test.py"
        temp_file.write_text(clean_code, encoding="utf-8")

        findings, telemetry = analyzer.analyze(str(temp_file), clean_code)

    assert len(findings) == 0
    assert telemetry.status == "completed"
    assert telemetry.findings_count == 0
