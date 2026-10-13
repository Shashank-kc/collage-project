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
import uuid
from typing import List

from app.config import ANALYSIS_TIMEOUT_SECONDS, RUFF_PATH
from app.schemas.analysis import Finding, FindingCategory, FindingSeverity
from app.services.recommendations import get_docs_for_rule, get_recommendation_for_rule

logger = logging.getLogger(__name__)


class RuffAnalyzer:
    """Invokes Ruff and parses its output into normalized Finding objects."""

    def __init__(self, executable_path: str = RUFF_PATH):
        self.executable_path = executable_path

    def analyze(self, file_path: str, source_code: str) -> List[Finding]:
        """
        Runs `ruff check <file_path> --output-format json` and returns findings.
        """
        findings: List[Finding] = []
        code_lines = source_code.splitlines()

        command = [
            self.executable_path,
            "check",
            file_path,
            "--output-format",
            "json",
            "--isolated"  # Prevent reading random parent pyproject.toml configs
        ]

        try:
            # subprocess.run executes the external binary in an isolated process.
            # Timeout is enforced to avoid hanging.
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=ANALYSIS_TIMEOUT_SECONDS,
                check=False  # Ruff exits with 1 when issues are found, which is expected
            )

            stdout = result.stdout.strip()
            if not stdout:
                # No findings or clean code
                return findings

            try:
                raw_findings = json.loads(stdout)
            except json.JSONDecodeError as exc:
                logger.error("Failed to decode Ruff JSON output: %s. Output was: %s", exc, stdout)
                return findings

            if not isinstance(raw_findings, list):
                return findings

            for item in raw_findings:
                rule_id = item.get("code") or "RUFF_ERR"
                message = item.get("message", "Code quality issue detected.")
                location = item.get("location") or {}
                end_location = item.get("end_location") or {}

                row = location.get("row")
                col = location.get("column")
                end_row = end_location.get("row")
                end_col = end_location.get("column")

                # Extract the relevant line snippet from user code
                snippet = None
                if row is not None and 1 <= row <= len(code_lines):
                    snippet = code_lines[row - 1].strip()

                category = self._categorize(rule_id)
                severity = self._determine_severity(rule_id)
                recommendation = get_recommendation_for_rule(rule_id, message)
                doc_url = item.get("url") or get_docs_for_rule(rule_id)

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
                        recommendation=recommendation,
                        documentation_url=doc_url,
                    )
                )

        except subprocess.TimeoutExpired:
            logger.warning("Ruff analysis timed out after %s seconds", ANALYSIS_TIMEOUT_SECONDS)
            findings.append(
                Finding(
                    id=f"ruff-timeout-{uuid.uuid4().hex[:8]}",
                    tool="ruff",
                    category=FindingCategory.QUALITY,
                    rule_id="TIMEOUT",
                    message="Ruff analysis timed out. The code submission may be excessively complex.",
                    severity=FindingSeverity.LOW,
                    recommendation="Try analyzing smaller functions or modules incrementally."
                )
            )
        except Exception as exc:
            logger.exception("Unexpected error while running Ruff: %s", exc)

        return findings

    def _categorize(self, rule_id: str) -> FindingCategory:
        """Categorizes finding based on Ruff rule prefix."""
        rule_upper = rule_id.upper()
        if rule_upper.startswith("E") or rule_upper.startswith("W"):
            return FindingCategory.STYLE
        if rule_upper.startswith("S"):
            return FindingCategory.SECURITY
        if "SYNTAX" in rule_upper or rule_upper.startswith("E9"):
            return FindingCategory.SYNTAX
        return FindingCategory.QUALITY

    def _determine_severity(self, rule_id: str) -> FindingSeverity:
        """Maps rule codes to a standardized severity level."""
        rule_upper = rule_id.upper()

        # Syntax errors & undefined names are severe defects
        if "SYNTAX" in rule_upper or rule_upper.startswith("E9") or rule_upper in ("F821", "F822"):
            return FindingSeverity.HIGH

        # Bugbear and runtime-impacting flaws
        if rule_upper.startswith("B"):
            return FindingSeverity.MEDIUM

        # Pyflakes unused variables / imports
        if rule_upper in ("F401", "F841"):
            return FindingSeverity.LOW

        # Style warnings
        if rule_upper.startswith("E") or rule_upper.startswith("W"):
            return FindingSeverity.INFO

        return FindingSeverity.LOW
