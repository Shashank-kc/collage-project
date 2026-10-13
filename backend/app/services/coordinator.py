"""
CodeGuard AI - Analysis Coordinator Service
============================================
Coordinates the multi-tool static analysis pipeline:
1. Creates an isolated temporary file for the submitted Python code.
2. Runs Ruff (Code Quality & Syntax) and Bandit (Security).
3. Merges, enriches, and sorts findings.
4. Calculates the Code Health Score and Grade.
5. Cleans up temporary resources safely.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import tempfile
import time
from typing import List, Tuple

from app.schemas.analysis import (
    AnalysisSummary,
    CodeAnalysisResponse,
    Finding,
    FindingCategory,
    FindingSeverity,
)
from app.services.bandit_analyzer import BanditAnalyzer
from app.services.ruff_analyzer import RuffAnalyzer

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {
    FindingSeverity.CRITICAL: 0,
    FindingSeverity.HIGH: 1,
    FindingSeverity.MEDIUM: 2,
    FindingSeverity.LOW: 3,
    FindingSeverity.INFO: 4,
}


class AnalysisCoordinator:
    """Coordinates static analysis tools and calculates overall quality metrics."""

    def __init__(self):
        self.ruff_analyzer = RuffAnalyzer()
        self.bandit_analyzer = BanditAnalyzer()

    def run_analysis(self, source_code: str, filename: str = "submission.py") -> CodeAnalysisResponse:
        """
        Runs the full analysis pipeline on the provided source code.
        """
        start_time = time.perf_counter()
        code_lines = source_code.splitlines()
        lines_analyzed = max(len(code_lines), 1)

        findings: List[Finding] = []

        # Create an isolated temporary directory to ensure safe sandboxed file operations
        with tempfile.TemporaryDirectory(prefix="codeguard_") as temp_dir:
            temp_file = Path(temp_dir) / "submission.py"
            # Write source code to the temp file
            temp_file.write_text(source_code, encoding="utf-8")

            # Execute Ruff analyzer
            try:
                ruff_findings = self.ruff_analyzer.analyze(str(temp_file), source_code)
                findings.extend(ruff_findings)
            except Exception as exc:
                logger.error("Ruff analyzer failed: %s", exc)

            # Execute Bandit analyzer
            try:
                bandit_findings = self.bandit_analyzer.analyze(str(temp_file), source_code)
                findings.extend(bandit_findings)
            except Exception as exc:
                logger.error("Bandit analyzer failed: %s", exc)

        # Sort findings: first by line number (asc), then by severity priority
        findings.sort(key=lambda f: (f.line or 999999, SEVERITY_ORDER.get(f.severity, 99)))

        # Compute summary and health score
        summary = self._compute_summary(findings)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return CodeAnalysisResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            execution_time_ms=elapsed_ms,
            lines_analyzed=lines_analyzed,
            summary=summary,
            findings=findings,
            disclaimer="Static analysis inspects code structure without execution. While it identifies common vulnerabilities and code defects, it does not guarantee 100% bug-free or secure software."
        )

    def _compute_summary(self, findings: List[Finding]) -> AnalysisSummary:
        """
        Aggregates finding counts and calculates the overall health score & grade.
        """
        total = len(findings)
        security_count = sum(1 for f in findings if f.category == FindingCategory.SECURITY)
        quality_count = sum(1 for f in findings if f.category in (FindingCategory.QUALITY, FindingCategory.STYLE, FindingCategory.SYNTAX))

        critical_count = sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL)
        high_count = sum(1 for f in findings if f.severity == FindingSeverity.HIGH)
        medium_count = sum(1 for f in findings if f.severity == FindingSeverity.MEDIUM)
        low_count = sum(1 for f in findings if f.severity == FindingSeverity.LOW)
        info_count = sum(1 for f in findings if f.severity == FindingSeverity.INFO)

        score, grade = self._calculate_health_score(
            critical_count, high_count, medium_count, low_count, info_count
        )

        return AnalysisSummary(
            total_findings=total,
            security_findings=security_count,
            quality_findings=quality_count,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            info_count=info_count,
            health_score=score,
            health_grade=grade,
        )

    def _calculate_health_score(
        self,
        critical: int,
        high: int,
        medium: int,
        low: int,
        info: int
    ) -> Tuple[int, str]:
        """
        Calculates health score (0-100) based on severity deductions.
        """
        deductions = (
            critical * 25 +
            high * 15 +
            medium * 8 +
            low * 3 +
            info * 1
        )
        score = max(0, 100 - deductions)

        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"

        return score, grade
