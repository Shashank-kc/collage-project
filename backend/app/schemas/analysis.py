"""
CodeGuard AI - Data Schemas (Pydantic Models)
=============================================
Defines the request and response data structures used by FastAPI.
Pydantic automatically validates types, handles serialization to JSON,
and generates OpenAPI documentation.
"""

from enum import Enum
from typing import List, Optional
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
    message: str = Field(description="Human-readable explanation of the issue")
    severity: FindingSeverity = Field(description="Severity rating")
    line: Optional[int] = Field(default=None, description="Line number where the issue was found (1-indexed)")
    column: Optional[int] = Field(default=None, description="Column number (1-indexed)")
    end_line: Optional[int] = Field(default=None, description="Ending line number if available")
    end_column: Optional[int] = Field(default=None, description="Ending column number if available")
    code_snippet: Optional[str] = Field(default=None, description="Code snippet where the issue occurred")
    recommendation: Optional[str] = Field(default=None, description="Suggested remedy or best practice for Python developers")
    documentation_url: Optional[str] = Field(default=None, description="Link to official rule documentation")


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


class CodeAnalysisResponse(BaseModel):
    scan_id: Optional[int] = Field(default=None, description="Unique ID saved in database history")
    timestamp: str = Field(description="ISO 8601 timestamp of analysis")
    execution_time_ms: float = Field(description="Time taken by the analysis pipeline in milliseconds")
    lines_analyzed: int = Field(description="Total lines of code analyzed")
    summary: AnalysisSummary = Field(description="High-level metrics and health grade")
    findings: List[Finding] = Field(default_factory=list, description="Detailed list of findings")
    disclaimer: str = Field(
        default="Static analysis checks code patterns without executing code. It is an automated aid and does not guarantee that code is free of all defects or security vulnerabilities."
    )


class ScanHistoryItem(BaseModel):
    id: int
    timestamp: str
    total_findings: int
    security_findings: int
    quality_findings: int
    health_score: int
    health_grade: str
    execution_time_ms: float
    code_preview: str
