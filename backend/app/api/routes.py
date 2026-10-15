"""
CodeGuard AI - API Endpoints
=============================
Defines the REST API routes for code analysis, scan history, metrics,
settings, health checks, and educational sample snippets.
"""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import (
    ANALYSIS_TIMEOUT_SECONDS,
    BANDIT_PATH,
    CORS_ORIGINS,
    MAX_CODE_SIZE_BYTES,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    RUFF_PATH,
)
from app.database.session import (
    get_dashboard_metrics,
    get_recent_scans,
    get_scan_by_id,
    save_scan_record,
)
from app.schemas.analysis import (
    CodeAnalysisRequest,
    CodeAnalysisResponse,
    DashboardMetrics,
    FindingExplanationRequest,
    FindingExplanationResponse,
    ScanComparisonRequest,
    ScanComparisonResponse,
    ScanHistoryItem,
    SettingsInfo,
    VerifyFixRequest,
    VerifyFixResponse,
)
from app.schemas.auth import UserResponse
from app.services.auth_service import get_optional_user
from app.services.coordinator import AnalysisCoordinator
from app.services.ai_explainer import ai_explainer

router = APIRouter(prefix="/api/v1", tags=["Analysis"])
coordinator = AnalysisCoordinator()

# Curated sample scripts for instant testing
SAMPLE_CODES = {
    "vulnerable": (
        'import os\n'
        'import sys\n'
        'import hashlib\n'
        '\n'
        '# Insecure database query simulation\n'
        'def get_user_profile(user_input_id):\n'
        '    # WARNING: SQL Injection vulnerability via string formatting\n'
        '    query = f"SELECT * FROM users WHERE id = {user_input_id}"\n'
        '    print("Executing:", query)\n'
        '\n'
        '# Hardcoded credentials\n'
        'DATABASE_PASSWORD = "super_secret_admin_password_123"\n'
        '\n'
        'def verify_token(token):\n'
        '    # Insecure use of assert in control flow\n'
        '    assert token is not None, "Token must exist"\n'
        '    \n'
        '    # Insecure hash algorithm (MD5)\n'
        '    token_hash = hashlib.md5(token.encode()).hexdigest()\n'
        '    return token_hash\n'
        '\n'
        'def run_calculation(expression):\n'
        '    # Dangerous dynamic code execution\n'
        '    return eval(expression)\n'
        '\n'
        'def process_items(items=[]):\n'
        '    # Mutable default argument bug\n'
        '    items.append(1)\n'
        '    return items\n'
    ),
    "clean": (
        '"""\n'
        'Clean, robust Python module demonstrating secure coding practices.\n'
        '"""\n'
        'from typing import List, Optional\n'
        'import hashlib\n'
        'import os\n'
        '\n'
        '\n'
        'def get_user_profile(user_id: int) -> dict:\n'
        '    """Uses parameterized queries to prevent SQL injection."""\n'
        '    # In a real app: cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))\n'
        '    return {"user_id": user_id, "status": "active"}\n'
        '\n'
        '\n'
        'def verify_token(token: str) -> str:\n'
        '    """Validates token using secure hashing (SHA-256)."""\n'
        '    if not token:\n'
        '        raise ValueError("Token must not be empty")\n'
        '    return hashlib.sha256(token.encode()).hexdigest()\n'
        '\n'
        '\n'
        'def get_database_password() -> Optional[str]:\n'
        '    """Reads credentials securely from environment variables."""\n'
        '    return os.getenv("DATABASE_PASSWORD")\n'
        '\n'
        '\n'
        'def append_item(item: int, items: Optional[List[int]] = None) -> List[int]:\n'
        '    """Avoids mutable default argument anti-pattern."""\n'
        '    if items is None:\n'
        '        items = []\n'
        '    items.append(item)\n'
        '    return items\n'
    )
}


@router.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(
    payload: CodeAnalysisRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
) -> CodeAnalysisResponse:
    """
    Submits Python source code for static analysis with Ruff and Bandit.
    Code is inspected strictly using static AST parsers and NEVER executed.
    Associates scan records with the authenticated user for data isolation.
    """
    raw_code = payload.code

    # Input validation: check for empty or whitespace-only code
    if not raw_code or not raw_code.strip():
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail="Source code cannot be empty."
        )

    # Input validation: payload size limitation
    code_bytes = len(raw_code.encode("utf-8"))
    if code_bytes > MAX_CODE_SIZE_BYTES:
        raise HTTPException(
            status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
            detail=f"Code size ({code_bytes} bytes) exceeds maximum limit of {MAX_CODE_SIZE_BYTES} bytes (100 KB)."
        )

    # Sanitize filename against path traversal
    safe_filename = Path(payload.filename).name if payload.filename else "submission.py"
    if not safe_filename or safe_filename in (".", ".."):
        safe_filename = "submission.py"

    # Execute static analysis pipeline with tool selections
    response = coordinator.run_analysis(
        source_code=raw_code,
        filename=safe_filename,
        enable_ruff=payload.enable_ruff,
        enable_bandit=payload.enable_bandit
    )

    # Check overall scanner status
    has_failed_scanner = any(s.status == "failed" for s in response.scanners)
    scan_status = "failed" if has_failed_scanner else "completed"

    # Persist summary to SQLite database, associating with user if authenticated
    try:
        user_id = current_user.id if current_user else None
        scan_id = save_scan_record(
            filename=safe_filename,
            lines_analyzed=response.lines_analyzed,
            health_score=response.summary.health_score,
            health_grade=response.summary.health_grade,
            total_findings=response.summary.total_findings,
            security_findings=response.summary.security_findings,
            quality_findings=response.summary.quality_findings,
            execution_time_ms=response.execution_time_ms,
            source_code=raw_code,
            status=scan_status,
            user_id=user_id
        )
        response.scan_id = scan_id
    except Exception as exc:
        print(f"Warning: Failed to save scan to database: {exc}")

    return response


@router.get("/metrics", response_model=DashboardMetrics)
async def get_metrics(
    current_user: Optional[UserResponse] = Depends(get_optional_user)
) -> DashboardMetrics:
    """Retrieves aggregated statistics from SQLite scan history isolated to the current user."""
    user_id = current_user.id if current_user else None
    return get_dashboard_metrics(user_id=user_id)


@router.get("/settings", response_model=SettingsInfo)
async def get_settings() -> SettingsInfo:
    """Returns genuine server configuration, scanner versions, and security limits."""
    return SettingsInfo(
        ruff_available=Path(RUFF_PATH).exists(),
        bandit_available=Path(BANDIT_PATH).exists(),
        ruff_path=RUFF_PATH,
        bandit_path=BANDIT_PATH,
        max_code_size_kb=MAX_CODE_SIZE_BYTES // 1024,
        timeout_seconds=ANALYSIS_TIMEOUT_SECONDS,
        rate_limit_requests=RATE_LIMIT_REQUESTS,
        rate_limit_window_seconds=RATE_LIMIT_WINDOW_SECONDS,
        cors_origins=CORS_ORIGINS,
        privacy_policy=(
            "CodeGuard AI performs pure static AST analysis. "
            "Submitted Python code is stored temporarily in isolated temporary files "
            "during inspection and deleted immediately after analysis. "
            "Only scan metadata and previews (up to 300 characters) are retained locally in SQLite."
        )
    )


@router.get("/history", response_model=List[ScanHistoryItem])
async def list_recent_scans(
    limit: int = 15,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
) -> List[ScanHistoryItem]:
    """Retrieves recent scan records from SQLite history isolated to the current user."""
    clamped_limit = max(1, min(limit, 50))
    user_id = current_user.id if current_user else None
    return get_recent_scans(limit=clamped_limit, user_id=user_id)


@router.get("/samples")
async def get_sample_codes():
    """Returns preset vulnerable and clean sample code for one-click testing."""
    return SAMPLE_CODES


@router.post("/verify-fix", response_model=VerifyFixResponse)
async def verify_fix_endpoint(payload: VerifyFixRequest) -> VerifyFixResponse:
    """
    Differentiating Feature: Fix Verification Engine (Explain. Fix. Verify.)
    Re-scans modified Python code to verify whether a finding has been resolved.
    """
    raw_code = payload.updated_code
    if not raw_code or not raw_code.strip():
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail="Updated code cannot be empty for fix verification."
        )

    code_bytes = len(raw_code.encode("utf-8"))
    if code_bytes > MAX_CODE_SIZE_BYTES:
        raise HTTPException(
            status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
            detail=f"Code size ({code_bytes} bytes) exceeds maximum limit of {MAX_CODE_SIZE_BYTES} bytes."
        )

    return coordinator.verify_fix(
        original_rule_id=payload.original_rule_id,
        updated_code=raw_code,
        original_line=payload.original_line,
        prior_score=payload.prior_score,
        prior_finding_count=payload.prior_finding_count,
        enable_ruff=payload.enable_ruff,
        enable_bandit=payload.enable_bandit
    )


@router.post("/compare-scans", response_model=ScanComparisonResponse)
async def compare_scans_endpoint(
    payload: ScanComparisonRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
) -> ScanComparisonResponse:
    """
    Compares two historical scans by their SQLite IDs to calculate resolved and remaining findings.
    Enforces authorization check: cannot compare scans belonging to another user.
    """
    if payload.base_scan_id is None or payload.subsequent_scan_id is None:
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail="Both base_scan_id and subsequent_scan_id must be provided."
        )

    user_id = current_user.id if current_user else None
    base = get_scan_by_id(payload.base_scan_id, user_id=user_id)
    subsequent = get_scan_by_id(payload.subsequent_scan_id, user_id=user_id)

    if not base or not subsequent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both of the specified scans could not be found or access is unauthorized."
        )

    score_delta = subsequent.health_score - base.health_score
    resolved_count = max(0, base.total_findings - subsequent.total_findings) if subsequent.total_findings <= base.total_findings else 0
    new_count = max(0, subsequent.total_findings - base.total_findings)
    remaining_count = min(base.total_findings, subsequent.total_findings)

    return ScanComparisonResponse(
        base_scan_id=payload.base_scan_id,
        subsequent_scan_id=payload.subsequent_scan_id,
        resolved_count=resolved_count,
        remaining_count=remaining_count,
        new_count=new_count,
        score_delta=score_delta
    )


@router.post("/explain-finding", response_model=FindingExplanationResponse)
async def explain_finding(payload: FindingExplanationRequest) -> FindingExplanationResponse:
    """
    Optional AI-assisted mentor explanation for a specific static analysis finding.
    Strictly isolated and clearly identified as advisory.
    """
    explanation, is_ai = ai_explainer.explain(
        rule_id=payload.rule_id,
        message=payload.message,
        code_snippet=payload.code_snippet
    )
    return FindingExplanationResponse(
        rule_id=payload.rule_id,
        explanation=explanation,
        is_ai_generated=is_ai
    )


@router.get("/health")
async def health_check():
    """Health check endpoint confirming service status and tool availability."""
    return {
        "status": "healthy",
        "service": "CodeGuard AI Backend",
        "tools": {
            "ruff": {"configured_path": RUFF_PATH, "available": Path(RUFF_PATH).exists()},
            "bandit": {"configured_path": BANDIT_PATH, "available": Path(BANDIT_PATH).exists()},
        }
    }
