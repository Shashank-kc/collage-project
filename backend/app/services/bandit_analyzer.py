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
import uuid
from typing import List

from app.config import ANALYSIS_TIMEOUT_SECONDS, BANDIT_PATH
from app.schemas.analysis import Finding, FindingCategory, FindingSeverity
from app.services.recommendations import get_docs_for_rule, get_recommendation_for_rule

logger = logging.getLogger(__name__)


class BanditAnalyzer:
    """Invokes Bandit CLI and transforms security scan results into normalized Findings."""

    def __init__(self, executable_path: str = BANDIT_PATH):
        self.executable_path = executable_path

    def analyze(self, file_path: str, source_code: str) -> List[Finding]:
        """
        Runs `bandit -f json -q <file_path>` and returns normalized findings.
        """
        findings: List[Finding] = []
        code_lines = source_code.splitlines()

        command = [
            self.executable_path,
            "-f",
            "json",
            "-q",  # Quiet mode: suppress banners, output pure json
            file_path
        ]

        try:
            # Execute Bandit in an isolated subprocess with a strict timeout
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=ANALYSIS_TIMEOUT_SECONDS,
                check=False  # Bandit exits with 1 if issues found
            )

            stdout = result.stdout.strip()
            if not stdout:
                return findings

            try:
                data = json.loads(stdout)
            except json.JSONDecodeError as exc:
                logger.error("Failed to decode Bandit JSON output: %s. Output was: %s", exc, stdout)
                return findings

            raw_results = data.get("results", [])
            for item in raw_results:
                rule_id = item.get("test_id", "BANDIT_SEC")
                message = item.get("issue_text", "Security vulnerability detected.")
                raw_severity = item.get("issue_severity", "MEDIUM").upper()
                raw_confidence = item.get("issue_confidence", "MEDIUM").upper()
                line_no = item.get("line_number")

                # Extract line snippet
                snippet = None
                if line_no is not None and 1 <= line_no <= len(code_lines):
                    snippet = code_lines[line_no - 1].strip()
                elif item.get("code"):
                    snippet = item.get("code").strip()

                # Map Bandit severity & confidence to standard severity
                severity = self._map_severity(raw_severity, raw_confidence)
                recommendation = get_recommendation_for_rule(rule_id, message)
                doc_url = item.get("more_info") or get_docs_for_rule(rule_id)

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
                        recommendation=recommendation,
                        documentation_url=doc_url,
                    )
                )

        except subprocess.TimeoutExpired:
            logger.warning("Bandit analysis timed out after %s seconds", ANALYSIS_TIMEOUT_SECONDS)
            findings.append(
                Finding(
                    id=f"bandit-timeout-{uuid.uuid4().hex[:8]}",
                    tool="bandit",
                    category=FindingCategory.SECURITY,
                    rule_id="TIMEOUT",
                    message="Bandit security analysis timed out.",
                    severity=FindingSeverity.LOW,
                    recommendation="Ensure code does not contain deeply recursive structures."
                )
            )
        except Exception as exc:
            logger.exception("Unexpected error while running Bandit: %s", exc)

        return findings

    def _map_severity(self, raw_severity: str, raw_confidence: str) -> FindingSeverity:
        """
        Combines severity and confidence to determine overall risk level.
        High severity with High confidence -> CRITICAL.
        """
        if raw_severity == "HIGH":
            if raw_confidence == "HIGH":
                return FindingSeverity.CRITICAL
            return FindingSeverity.HIGH
        elif raw_severity == "MEDIUM":
            return FindingSeverity.MEDIUM
        elif raw_severity == "LOW":
            return FindingSeverity.LOW
        return FindingSeverity.INFO
