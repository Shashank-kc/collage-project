"""
CodeGuard AI - Bandit Security Analyzer Service
================================================
Executes OpenStack Bandit against Python source code to detect security
vulnerabilities and dangerous coding patterns using Python's AST parser.

IMPORTANT ARCHITECTURAL RULE:
Code is NEVER executed or imported by this analyzer. Only static AST
inspection is performed.
"""

import json
import logging
import subprocess
import time
import uuid
from typing import List, Tuple

from app.config import ANALYSIS_TIMEOUT_SECONDS, BANDIT_PATH
from app.schemas.analysis import Finding, FindingCategory, FindingSeverity, ScannerTelemetry
from app.services.recommendations import get_rule_details

logger = logging.getLogger(__name__)


class BanditAnalyzer:
    """Invokes Bandit CLI and transforms security scan results into normalized Findings with telemetry."""

    def __init__(self, executable_path: str = BANDIT_PATH):
        self.executable_path = executable_path

    def analyze(self, file_path: str, source_code: str) -> Tuple[List[Finding], ScannerTelemetry]:
        """
        Runs `bandit -f json -q <file_path>` and returns (findings, telemetry).
        """
        start = time.perf_counter()
        findings: List[Finding] = []
        code_lines = source_code.splitlines()

        command = [
            self.executable_path,
            "-f",
            "json",
            "-q",
            file_path
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
                    name="bandit",
                    status="completed",
                    duration_ms=duration_ms,
                    findings_count=0
                )

            try:
                data = json.loads(stdout)
            except json.JSONDecodeError as exc:
                logger.error("Failed to decode Bandit JSON output: %s", exc)
                return findings, ScannerTelemetry(
                    name="bandit",
                    status="failed",
                    duration_ms=duration_ms,
                    findings_count=0,
                    error_message=f"Invalid JSON emitted by Bandit: {exc}"
                )

            raw_results = data.get("results", [])
            for item in raw_results:
                rule_id = item.get("test_id", "BANDIT_SEC")
                message = item.get("issue_text", "Security vulnerability detected.")
                raw_severity = item.get("issue_severity", "MEDIUM").upper()
                raw_confidence = item.get("issue_confidence", "MEDIUM").upper()
                line_no = item.get("line_number")

                snippet = None
                if line_no is not None and 1 <= line_no <= len(code_lines):
                    snippet = code_lines[line_no - 1].strip()
                elif item.get("code"):
                    snippet = item.get("code").strip()

                severity = self._map_severity(raw_severity, raw_confidence)
                why_it_matters, recommendation, doc_url = get_rule_details(rule_id, message)
                if item.get("more_info"):
                    doc_url = item.get("more_info")

                findings.append(
                    Finding(
                        id=f"bandit-{uuid.uuid4().hex[:8]}",
                        tool="bandit",
                        category=FindingCategory.SECURITY,
                        rule_id=rule_id,
                        message=message,
                        severity=severity,
                        line=line_no,
                        column=None,
                        code_snippet=snippet,
                        why_it_matters=why_it_matters,
                        recommendation=recommendation,
                        documentation_url=doc_url,
                    )
                )

            return findings, ScannerTelemetry(
                name="bandit",
                status="completed",
                duration_ms=duration_ms,
                findings_count=len(findings)
            )

        except subprocess.TimeoutExpired:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.warning("Bandit analysis timed out after %s seconds", ANALYSIS_TIMEOUT_SECONDS)
            findings.append(
                Finding(
                    id=f"bandit-timeout-{uuid.uuid4().hex[:8]}",
                    tool="bandit",
                    category=FindingCategory.SECURITY,
                    rule_id="TIMEOUT",
                    message="Bandit security analysis timed out.",
                    severity=FindingSeverity.LOW,
                    why_it_matters="Execution limits protect server resources from hanging on pathological input.",
                    recommendation="Ensure code does not contain deeply recursive structures."
                )
            )
            return findings, ScannerTelemetry(
                name="bandit",
                status="timed_out",
                duration_ms=duration_ms,
                findings_count=1,
                error_message=f"Process timed out after {ANALYSIS_TIMEOUT_SECONDS}s"
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception("Unexpected error while running Bandit: %s", exc)
            return findings, ScannerTelemetry(
                name="bandit",
                status="failed",
                duration_ms=duration_ms,
                findings_count=0,
                error_message=str(exc)
            )

    def _map_severity(self, raw_severity: str, raw_confidence: str) -> FindingSeverity:
        if raw_severity == "HIGH":
            if raw_confidence == "HIGH":
                return FindingSeverity.CRITICAL
            return FindingSeverity.HIGH
        elif raw_severity == "MEDIUM":
            return FindingSeverity.MEDIUM
        elif raw_severity == "LOW":
            return FindingSeverity.LOW
        return FindingSeverity.INFO
