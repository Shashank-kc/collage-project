"""
CodeGuard AI - Data Schemas (Pydantic Models)
=============================================
Defines the request and response data structures used by FastAPI.
Includes educational explanations, telemetry per tool, and dashboard metrics.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FindingCategory(str, Enum):
    SECURITY = "security"
    QUALITY = "quality"
    STYLE = "style"
    SYNTAX = "syntax"


class Finding(BaseModel):
    id: str = Field(description="Unique identifier for this finding")
    tool: str = Field(description="Static analysis tool that reported the issue ('ruff' or 'bandit')")
    category: FindingCategory = Field(description="Category of the finding")
    rule_id: str = Field(description="Tool rule code (e.g., B608, F401, E501)")
    message: str = Field(description="Human-readable description of the issue")
    severity: FindingSeverity = Field(description="Severity rating")
    line: Optional[int] = Field(default=None, description="Line number where the issue was found (1-indexed)")
    column: Optional[int] = Field(default=None, description="Column number (1-indexed)")
    end_line: Optional[int] = Field(default=None, description="Ending line number if available")
    end_column: Optional[int] = Field(default=None, description="Ending column number if available")
    code_snippet: Optional[str] = Field(default=None, description="Code snippet where the issue occurred")
    what_detected: Optional[str] = Field(
        default=None,
        description="Plain-English summary of what AST defect or pattern was detected"
    )
    why_it_matters: Optional[str] = Field(
        default=None,
        description="Educational explanation detailing the security/architectural impact of this issue"
    )
    where_is_it: Optional[str] = Field(
        default=None,
        description="Human-readable location description (file and line)"
    )
    how_to_improve: Optional[str] = Field(
        default=None,
        description="Concrete remediation recommendation for Python developers"
    )
    safer_example: Optional[str] = Field(
        default=None,
        description="Code example demonstrating a safer, PEP-8 compliant approach"
    )
    verification_guide: Optional[str] = Field(
        default=None,
        description="Instructions on how to verify that this issue has been resolved"
    )
    recommendation: Optional[str] = Field(
        default=None,
        description="Legacy alias for how_to_improve"
    )
    documentation_url: Optional[str] = Field(
        default=None,
        description="Link to official rule documentation"
    )


class ScannerTelemetry(BaseModel):
    name: str = Field(description="Scanner name ('ruff' or 'bandit')")
    status: str = Field(description="Execution status ('completed', 'failed', 'timed_out', 'disabled')")
    duration_ms: float = Field(description="Time taken by this specific scanner in milliseconds")
    findings_count: int = Field(description="Number of findings discovered by this scanner")
    error_message: Optional[str] = Field(default=None, description="Error message if the scanner failed")


class AnalysisSummary(BaseModel):
    total_findings: int = 0
    security_findings: int = 0
    quality_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    health_score: int = Field(description="Code health score between 0 and 100")
    health_grade: str = Field(description="Health grade: A, B, C, D, or F")


class CodeAnalysisRequest(BaseModel):
    code: str = Field(
        ...,
        min_length=1,
        description="Python source code to analyze"
    )
    filename: Optional[str] = Field(
        default="submission.py",
        description="Optional display filename"
    )
    enable_ruff: bool = Field(
        default=True,
        description="Whether to execute Ruff code quality scanner"
    )
    enable_bandit: bool = Field(
        default=True,
        description="Whether to execute Bandit security scanner"
    )


class CodeAnalysisResponse(BaseModel):
    scan_id: Optional[int] = Field(default=None, description="Unique ID saved in database history")
    timestamp: str = Field(description="ISO 8601 timestamp of analysis")
    execution_time_ms: float = Field(description="Total time taken by the analysis pipeline in milliseconds")
    lines_analyzed: int = Field(description="Total lines of code analyzed")
    scanners: List[ScannerTelemetry] = Field(
        default_factory=list,
        description="Telemetry and status for each configured scanner"
    )
    summary: AnalysisSummary = Field(description="High-level metrics and health grade")
    findings: List[Finding] = Field(default_factory=list, description="Detailed list of findings")
    disclaimer: str = Field(
        default="Static analysis inspects code structure without execution. While it identifies common vulnerabilities and code defects, it does not guarantee 100% bug-free or secure software."
    )


class ScanHistoryItem(BaseModel):
    id: int
    timestamp: str
    status: str = "completed"
    total_findings: int
    security_findings: int
    quality_findings: int
    health_score: int
    health_grade: str
    execution_time_ms: float
    code_preview: str


class DashboardMetrics(BaseModel):
    total_scans: int
    completed_scans: int
    failed_scans: int
    average_health_score: float
    total_security_issues: int
    total_quality_issues: int
    grade_distribution: Dict[str, int]
    recent_scans: List[ScanHistoryItem]


class SettingsInfo(BaseModel):
    ruff_available: bool
    bandit_available: bool
    ruff_path: str
    bandit_path: str
    max_code_size_kb: int
    timeout_seconds: int
    rate_limit_requests: int
    rate_limit_window_seconds: int
    cors_origins: List[str]
    privacy_policy: str


class FindingExplanationRequest(BaseModel):
    rule_id: str
    message: str
    code_snippet: Optional[str] = None


class FindingExplanationResponse(BaseModel):
    rule_id: str
    explanation: str
    is_ai_generated: bool
    disclaimer: str = (
        "AI-generated recommendations are advisory and must be reviewed by an engineer prior to implementation."
    )


class VerificationStatus(str, Enum):
    RESOLVED = "RESOLVED"
    STILL_DETECTED = "STILL_DETECTED"
    NEW_FINDING = "NEW_FINDING"
    INCONCLUSIVE = "INCONCLUSIVE"


class VerifyFixRequest(BaseModel):
    original_rule_id: str
    original_line: Optional[int] = None
    prior_score: int = 100
    prior_finding_count: int = 1
    updated_code: str = Field(..., min_length=1)
    enable_ruff: bool = True
    enable_bandit: bool = True


class VerifyFixResponse(BaseModel):
    status: VerificationStatus
    rule_id: str
    message: str
    health_score_delta: int
    prior_score: int
    new_score: int
    prior_finding_count: int
    new_finding_count: int
    subsequent_analysis: CodeAnalysisResponse
    disclaimer: str = (
        "Fix verification re-analyzes modified source code. "
        "A RESOLVED finding indicates the specific static rule is no longer detected, "
        "but does not guarantee complete absence of all runtime bugs or security risks."
    )


class ScanComparisonRequest(BaseModel):
    base_scan_id: Optional[int] = None
    subsequent_scan_id: Optional[int] = None


class ScanComparisonResponse(BaseModel):
    base_scan_id: Optional[int] = None
    subsequent_scan_id: Optional[int] = None
    resolved_count: int
    remaining_count: int
    new_count: int
    score_delta: int
    disclaimer: str = (
        "Comparison evaluates changes between two discrete static analysis scans. "
        "Different tool configurations or rule settings between scans may affect results."
    )

