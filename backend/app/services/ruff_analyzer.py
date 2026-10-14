"""
CodeGuard AI - Ruff Static Analyzer Service
============================================
Executes Astral's Ruff linter against Python code files via subprocess.
Ruff is written in Rust and performs extremely fast AST-based linting.

IMPORTANT ARCHITECTURAL RULE:
Code is NEVER executed or imported by this analyzer. Only static AST parsing
and rule checks are performed.
"""

import json
import logging
import subprocess
import time
import uuid
from typing import List, Tuple

from app.config import ANALYSIS_TIMEOUT_SECONDS, RUFF_PATH
from app.schemas.analysis import Finding, FindingCategory, FindingSeverity, ScannerTelemetry
from app.services.recommendations import get_rule_details, get_rule_details_structured

logger = logging.getLogger(__name__)


class RuffAnalyzer:
    """Invokes Ruff and parses its output into normalized Finding objects with telemetry."""

    def __init__(self, executable_path: str = RUFF_PATH):
        self.executable_path = executable_path

    def analyze(self, file_path: str, source_code: str) -> Tuple[List[Finding], ScannerTelemetry]:
        """
        Runs `ruff check <file_path> --output-format json` and returns (findings, telemetry).
        """
        start = time.perf_counter()
        findings: List[Finding] = []
        code_lines = source_code.splitlines()

        command = [
            self.executable_path,
            "check",
            file_path,
            "--output-format",
            "json",
            "--isolated"
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=ANALYSIS_TIMEOUT_SECONDS,
                check=False
            )

            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            stdout = result.stdout.strip()

            if not stdout:
                return findings, ScannerTelemetry(
                    name="ruff",
                    status="completed",
                    duration_ms=duration_ms,
                    findings_count=0
                )

            try:
                raw_findings = json.loads(stdout)
            except json.JSONDecodeError as exc:
                logger.error("Failed to decode Ruff JSON output: %s", exc)
                return findings, ScannerTelemetry(
                    name="ruff",
                    status="failed",
                    duration_ms=duration_ms,
                    findings_count=0,
                    error_message=f"Invalid JSON emitted by Ruff: {exc}"
                )

            if isinstance(raw_findings, list):
                for item in raw_findings:
                    rule_id = item.get("code") or "RUFF_ERR"
                    message = item.get("message", "Code quality issue detected.")
                    location = item.get("location") or {}
                    end_location = item.get("end_location") or {}

                    row = location.get("row")
                    col = location.get("column")
                    end_row = end_location.get("row")
                    end_col = end_location.get("column")

                    snippet = None
                    if row is not None and 1 <= row <= len(code_lines):
                        snippet = code_lines[row - 1].strip()

                    category = self._categorize(rule_id)
                    severity = self._determine_severity(rule_id)
                    structured_details = get_rule_details_structured(rule_id, message, filename="submission.py", line=row)
                    doc_url = item.get("url") or structured_details.get("docs")

                    findings.append(
                        Finding(
                            id=f"ruff-{uuid.uuid4().hex[:8]}",
                            tool="ruff",
                            category=category,
                            rule_id=rule_id,
                            message=message,
                            severity=severity,
                            line=row,
                            column=col,
                            end_line=end_row,
                            end_column=end_col,
                            code_snippet=snippet,
                            what_detected=structured_details.get("what_detected"),
                            why_it_matters=structured_details.get("why_it_matters"),
                            where_is_it=structured_details.get("where_is_it"),
                            how_to_improve=structured_details.get("how_to_improve"),
                            safer_example=structured_details.get("safer_example"),
                            verification_guide=structured_details.get("verification_guide"),
                            recommendation=structured_details.get("how_to_improve"),
                            documentation_url=doc_url,
                        )
                    )

            return findings, ScannerTelemetry(
                name="ruff",
                status="completed",
                duration_ms=duration_ms,
                findings_count=len(findings)
            )

        except subprocess.TimeoutExpired:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.warning("Ruff analysis timed out after %s seconds", ANALYSIS_TIMEOUT_SECONDS)
            findings.append(
                Finding(
                    id=f"ruff-timeout-{uuid.uuid4().hex[:8]}",
                    tool="ruff",
                    category=FindingCategory.QUALITY,
                    rule_id="TIMEOUT",
                    message="Ruff analysis timed out. The submitted file was too complex to process within the limit.",
                    severity=FindingSeverity.LOW,
                    why_it_matters="Execution limits protect server resources from hanging on pathological input.",
                    recommendation="Try analyzing smaller functions or modules incrementally."
                )
            )
            return findings, ScannerTelemetry(
                name="ruff",
                status="timed_out",
                duration_ms=duration_ms,
                findings_count=1,
                error_message=f"Process timed out after {ANALYSIS_TIMEOUT_SECONDS}s"
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception("Unexpected error while running Ruff: %s", exc)
            return findings, ScannerTelemetry(
                name="ruff",
                status="failed",
                duration_ms=duration_ms,
                findings_count=0,
                error_message=str(exc)
            )

    def _categorize(self, rule_id: str) -> FindingCategory:
        rule_upper = rule_id.upper()
        if rule_upper.startswith("E") or rule_upper.startswith("W"):
            return FindingCategory.STYLE
        if rule_upper.startswith("S"):
            return FindingCategory.SECURITY
        if "SYNTAX" in rule_upper or rule_upper.startswith("E9"):
            return FindingCategory.SYNTAX
        return FindingCategory.QUALITY

    def _determine_severity(self, rule_id: str) -> FindingSeverity:
        rule_upper = rule_id.upper()
        if "SYNTAX" in rule_upper or rule_upper.startswith("E9") or rule_upper in ("F821", "F822"):
            return FindingSeverity.HIGH
        if rule_upper.startswith("B"):
            return FindingSeverity.MEDIUM
        if rule_upper in ("F401", "F841"):
            return FindingSeverity.LOW
        if rule_upper.startswith("E") or rule_upper.startswith("W"):
            return FindingSeverity.INFO
        return FindingSeverity.LOW
