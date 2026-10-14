"""
CodeGuard AI - Analysis Coordinator Service
============================================
Coordinates the multi-tool static analysis pipeline:
1. Creates an isolated temporary directory for the submitted Python code.
2. Invokes configured scanners (Ruff and/or Bandit) safely via subprocess.
3. Collects telemetry, execution timings, and findings per tool.
4. Calculates the documented Code Health Score and Grade.
5. Cleans up all temporary resources safely.

HEALTH SCORE CALCULATION METHODOLOGY:
-------------------------------------
The score starts at 100 points. Points are deducted based on findings:
- CRITICAL severity: -25 pts (Active security exploit or remote execution vector)
- HIGH severity:     -15 pts (High-confidence vulnerability or syntax crash)
- MEDIUM severity:   -8 pts  (Flaw, assertion in production, or bugbear anti-pattern)
- LOW severity:      -3 pts  (Unused import, dead variable, or minor flaw)
- INFO severity:     -1 pt   (PEP 8 formatting or style recommendation)

Score is clamped to [0, 100].
Grades: A (>=90), B (>=80), C (>=70), D (>=60), F (<60).
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import tempfile
import time
from typing import List, Optional, Tuple

from app.schemas.analysis import (
    AnalysisSummary,
    CodeAnalysisResponse,
    Finding,
    FindingCategory,
    FindingSeverity,
    ScannerTelemetry,
    ScanComparisonResponse,
    VerificationStatus,
    VerifyFixResponse,
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

    def run_analysis(
        self,
        source_code: str,
        filename: str = "submission.py",
        enable_ruff: bool = True,
        enable_bandit: bool = True
    ) -> CodeAnalysisResponse:
        """
        Runs the static analysis pipeline on the provided source code.
        Never executes or evaluates the code.
        """
        start_time = time.perf_counter()
        code_lines = source_code.splitlines()
        lines_analyzed = max(len(code_lines), 1)

        findings: List[Finding] = []
        scanners_telemetry: List[ScannerTelemetry] = []

        # Sanitize filename to prevent directory traversal
        safe_filename = Path(filename).name if filename else "submission.py"
        if not safe_filename or safe_filename in (".", ".."):
            safe_filename = "submission.py"

        # Create an isolated temporary directory for safe file inspection
        with tempfile.TemporaryDirectory(prefix="codeguard_") as temp_dir:
            temp_file = Path(temp_dir) / safe_filename
            temp_file.write_text(source_code, encoding="utf-8")

            # 1. Execute Ruff Analyzer (Quality, Syntax, Formatting)
            if enable_ruff:
                try:
                    ruff_findings, ruff_telemetry = self.ruff_analyzer.analyze(
                        str(temp_file), source_code
                    )
                    findings.extend(ruff_findings)
                    scanners_telemetry.append(ruff_telemetry)
                except Exception as exc:
                    logger.error("Ruff execution error: %s", exc)
                    scanners_telemetry.append(
                        ScannerTelemetry(
                            name="ruff",
                            status="failed",
                            duration_ms=0.0,
                            findings_count=0,
                            error_message=str(exc)
                        )
                    )
            else:
                scanners_telemetry.append(
                    ScannerTelemetry(
                        name="ruff",
                        status="disabled",
                        duration_ms=0.0,
                        findings_count=0
                    )
                )

            # 2. Execute Bandit Analyzer (AST Security Vulnerabilities)
            if enable_bandit:
                try:
                    bandit_findings, bandit_telemetry = self.bandit_analyzer.analyze(
                        str(temp_file), source_code
                    )
                    findings.extend(bandit_findings)
                    scanners_telemetry.append(bandit_telemetry)
                except Exception as exc:
                    logger.error("Bandit execution error: %s", exc)
                    scanners_telemetry.append(
                        ScannerTelemetry(
                            name="bandit",
                            status="failed",
                            duration_ms=0.0,
                            findings_count=0,
                            error_message=str(exc)
                        )
                    )
            else:
                scanners_telemetry.append(
                    ScannerTelemetry(
                        name="bandit",
                        status="disabled",
                        duration_ms=0.0,
                        findings_count=0
                    )
                )

        # Sort findings: line number (asc), then severity priority
        findings.sort(key=lambda f: (f.line or 999999, SEVERITY_ORDER.get(f.severity, 99)))

        # Compute summary and health score
        summary = self._compute_summary(findings)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return CodeAnalysisResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            execution_time_ms=elapsed_ms,
            lines_analyzed=lines_analyzed,
            scanners=scanners_telemetry,
            summary=summary,
            findings=findings,
            disclaimer=(
                "Static analysis inspects code structure without execution. "
                "While it identifies common vulnerabilities and code defects, "
                "it does not guarantee 100% bug-free or secure software."
            )
        )

    def _compute_summary(self, findings: List[Finding]) -> AnalysisSummary:
        total = len(findings)
        security_count = sum(1 for f in findings if f.category == FindingCategory.SECURITY)
        quality_count = sum(
            1 for f in findings
            if f.category in (FindingCategory.QUALITY, FindingCategory.STYLE, FindingCategory.SYNTAX)
        )

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
        Documented, deterministic health score formula.
        Base: 100. Deductions per finding severity.
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

    def verify_fix(
        self,
        original_rule_id: str,
        updated_code: str,
        original_line: Optional[int] = None,
        prior_score: int = 100,
        prior_finding_count: int = 1,
        enable_ruff: bool = True,
        enable_bandit: bool = True
    ) -> VerifyFixResponse:
        """
        Differentiating Feature: Fix Verification Engine (Explain. Fix. Verify.)
        Re-scans the modified code and evaluates verification status:
        - RESOLVED: Target rule is no longer detected.
        - STILL_DETECTED: Target rule remains present.
        - INCONCLUSIVE: Scanner execution failed or timed out.
        - NEW_FINDING: Target rule resolved, but other defects were introduced.
        """
        analysis = self.run_analysis(
            source_code=updated_code,
            filename="verified_submission.py",
            enable_ruff=enable_ruff,
            enable_bandit=enable_bandit
        )

        has_failed = any(
            s.status in ("failed", "timed_out")
            for s in analysis.scanners
            if s.status != "disabled"
        )
        if has_failed:
            return VerifyFixResponse(
                status=VerificationStatus.INCONCLUSIVE,
                rule_id=original_rule_id,
                message="Fix verification was inconclusive because one or more static analysis tools failed or timed out.",
                health_score_delta=analysis.summary.health_score - prior_score,
                prior_score=prior_score,
                new_score=analysis.summary.health_score,
                prior_finding_count=prior_finding_count,
                new_finding_count=analysis.summary.total_findings,
                subsequent_analysis=analysis
            )

        # Check if original rule is still present in subsequent scan
        matching_findings = [
            f for f in analysis.findings
            if f.rule_id.upper() == original_rule_id.upper()
        ]

        score_delta = analysis.summary.health_score - prior_score
        new_finding_count = analysis.summary.total_findings

        if matching_findings:
            return VerifyFixResponse(
                status=VerificationStatus.STILL_DETECTED,
                rule_id=original_rule_id,
                message=f"Rule {original_rule_id} is still detected in the updated code ({len(matching_findings)} occurrence(s)). Review remediation guidance and adjust code.",
                health_score_delta=score_delta,
                prior_score=prior_score,
                new_score=analysis.summary.health_score,
                prior_finding_count=prior_finding_count,
                new_finding_count=new_finding_count,
                subsequent_analysis=analysis
            )

        if new_finding_count > 0 and prior_finding_count == 1:
            return VerifyFixResponse(
                status=VerificationStatus.NEW_FINDING,
                rule_id=original_rule_id,
                message=f"Original finding {original_rule_id} was resolved, but subsequent analysis detected {new_finding_count} other issue(s).",
                health_score_delta=score_delta,
                prior_score=prior_score,
                new_score=analysis.summary.health_score,
                prior_finding_count=prior_finding_count,
                new_finding_count=new_finding_count,
                subsequent_analysis=analysis
            )

        return VerifyFixResponse(
            status=VerificationStatus.RESOLVED,
            rule_id=original_rule_id,
            message=f"Rule {original_rule_id} successfully verified as resolved! Code health improved by {score_delta:+d} points.",
            health_score_delta=score_delta,
            prior_score=prior_score,
            new_score=analysis.summary.health_score,
            prior_finding_count=prior_finding_count,
            new_finding_count=new_finding_count,
            subsequent_analysis=analysis
        )

    def compare_scan_findings(
        self,
        base_findings: List[Finding],
        subsequent_findings: List[Finding],
        base_score: int,
        subsequent_score: int,
        base_scan_id: Optional[int] = None,
        subsequent_scan_id: Optional[int] = None
    ) -> ScanComparisonResponse:
        """Compares two sets of findings to compute resolved, remaining, and new findings."""
        base_rules = {f.rule_id.upper() for f in base_findings}
        subsequent_rules = {f.rule_id.upper() for f in subsequent_findings}

        resolved_count = len(base_rules - subsequent_rules)
        remaining_count = len(base_rules & subsequent_rules)
        new_count = len(subsequent_rules - base_rules)
        score_delta = subsequent_score - base_score

        return ScanComparisonResponse(
            base_scan_id=base_scan_id,
            subsequent_scan_id=subsequent_scan_id,
            resolved_count=resolved_count,
            remaining_count=remaining_count,
            new_count=new_count,
            score_delta=score_delta
        )
