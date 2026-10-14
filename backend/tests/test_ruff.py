"""
Unit Tests for Ruff Analyzer Service
"""

import tempfile
from pathlib import Path
from app.services.ruff_analyzer import RuffAnalyzer
from app.schemas.analysis import FindingCategory


def test_ruff_detects_unused_import():
    analyzer = RuffAnalyzer()
    sample_code = "import sys\nimport os\n\ndef add(a, b):\n    return a + b\n"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "test.py"
        temp_file.write_text(sample_code, encoding="utf-8")

        findings, telemetry = analyzer.analyze(str(temp_file), sample_code)

    # Should detect unused imports (F401)
    rule_ids = [f.rule_id for f in findings]
    assert "F401" in rule_ids
    assert any(f.category == FindingCategory.QUALITY for f in findings)
    assert telemetry.status == "completed"
    assert telemetry.findings_count > 0
    assert findings[0].why_it_matters is not None


def test_ruff_clean_code():
    analyzer = RuffAnalyzer()
    clean_code = "def greet(name: str) -> str:\n    return f'Hello, {name}'\n"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "test.py"
        temp_file.write_text(clean_code, encoding="utf-8")

        findings, telemetry = analyzer.analyze(str(temp_file), clean_code)

    # Should have no quality errors
    assert len(findings) == 0
    assert telemetry.status == "completed"
    assert telemetry.findings_count == 0
