"""
CodeGuard AI - Backend Configuration
====================================
Contains application settings, limits, and tool paths.
"""

from pathlib import Path
import shutil
import sys

# Base directories
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_PATH = BACKEND_DIR / "codeguard.db"

# Security & payload limits
# Prevent DoS attacks by restricting the size of analyzed code (max 100 KB)
MAX_CODE_SIZE_BYTES = 100 * 1024

# Subprocess timeout in seconds to prevent long-running hangs
ANALYSIS_TIMEOUT_SECONDS = 15

# Allowed CORS origins for frontend-backend communication
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "*"  # Permissive for local development
]

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
