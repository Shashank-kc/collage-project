"""
CodeGuard AI - Backend Configuration
====================================
Contains application settings, limits, security controls, and tool paths.
"""

from pathlib import Path
import os
import shutil
import sys
from typing import List

# Base directories
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_PATH = BACKEND_DIR / "codeguard.db"

# Security & payload limits
# Prevent Denial of Service (DoS) by restricting the maximum code size (100 KB)
MAX_CODE_SIZE_BYTES = 100 * 1024

# Subprocess execution timeout in seconds to prevent resource exhaustion/hanging
ANALYSIS_TIMEOUT_SECONDS = 15

# Rate limiting controls (per client IP)
# 30 requests per 60 seconds
RATE_LIMIT_REQUESTS = int(os.getenv("CODEGUARD_RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("CODEGUARD_RATE_LIMIT_WINDOW_SECONDS", "60"))

# Allowed CORS origins for frontend-backend communication
# In production, specify exact origins via CODEGUARD_CORS_ORIGINS (comma-separated).
# Wildcards are strictly avoided by default.
def get_cors_origins() -> List[str]:
    raw_env = os.getenv("CODEGUARD_CORS_ORIGINS", "")
    if raw_env.strip():
        return [origin.strip() for origin in raw_env.split(",") if origin.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

CORS_ORIGINS = get_cors_origins()

def get_executable_path(name: str) -> str:
    """
    Locates an executable (e.g., 'ruff' or 'bandit') in the current Python
    virtual environment or the system PATH.
    """
    # Check current virtual environment's Scripts (Windows) or bin (Linux/Mac)
    venv_dir = Path(sys.prefix)
    windows_bin = venv_dir / "Scripts" / f"{name}.exe"
    posix_bin = venv_dir / "bin" / name

    if windows_bin.exists():
        return str(windows_bin)
    if posix_bin.exists():
        return str(posix_bin)

    # Fallback to system PATH
    system_path = shutil.which(name)
    if system_path:
        return system_path

    # Default to just the command name
    return name

RUFF_PATH = get_executable_path("ruff")
BANDIT_PATH = get_executable_path("bandit")
