# CodeGuard AI 2.0 🛡️
> **Explain. Fix. Verify.**  
> *Production-Grade Python Static Analysis & Guided Remediation Platform*

CodeGuard AI 2.0 is a modern, developer-centric static analysis platform. It empowers engineers and students to inspect Python source code for security vulnerabilities, software defects, and style anti-patterns, understand why issues matter through structured educational insights, apply reviewable fixes, and verify resolutions with subsequent AST scans.

---

## 🌟 What's New in CodeGuard AI 2.0

1. **Explain. Fix. Verify. Framework**:
   - **What Was Detected?**: Clear plain-English summary of the AST flaw.
   - **Why Does It Matter?**: Realistic risk assessment without exaggeration.
   - **Where Is It?**: Precise source line and column markers.
   - **How Can It Be Improved?**: Concrete, actionable remediation guidance.
   - **Safer Code Pattern**: Production-ready code replacements.
   - **How Can I Verify?**: Step-by-step guidance for subsequent verification.
2. **Fix Verification Engine**:
   - Apply proposed code remedies to the active editor with one click.
   - Re-scan modified code and verify whether findings transitioned to:
     - `RESOLVED`: Target rule is no longer detected (+ health score gain).
     - `STILL_DETECTED`: Target rule remains present in modified code.
     - `NEW_FINDING`: Target rule cleared, but other defects were introduced.
     - `INCONCLUSIVE`: Subprocess execution timed out or failed.
3. **3-Panel Professional Workspace**:
   - **Left Panel**: Project explorer tree, preset test suites (Vulnerable vs Clean), active scanner indicators, and recent SQLite scans.
   - **Center Panel**: High-performance editor with synchronized line numbers, line gutter issue markers, and live byte size meter.
   - **Right Panel**: Searchable & sortable findings list + dedicated Fix Verification Inspector.
4. **Scan Comparison Engine**:
   - Compare any two historical scans from SQLite database.
   - Computes resolved findings, remaining findings, new issues, and health score delta.
5. **Security Hardening**:
   - **Zero Code Execution**: Code is parsed exclusively via static AST compilers (**Ruff** & **Bandit**). Code is never imported or evaluated.
   - **Directory Traversal Defense**: Strict filename sanitization using `Path(filename).name`.
   - **In-Memory Rate Limiting**: Sliding-window rate limiter per client IP.
   - **OWASP Security Headers**: Injects `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, and `Referrer-Policy`.
   - **Isolated Temporary File Sandboxing**: Code files are inspected within dedicated temporary directories with automatic cleanup.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Vanilla CSS Design System |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2 |
| **Security Scanner** | OpenStack Bandit (`bandit -f json`) |
| **Quality & Linter** | Astral Ruff (`ruff check --output-format json`) |
| **Database** | SQLite (built-in `sqlite3`) |
| **Testing** | Pytest, HTTPX (25 automated integration tests) |

---

## 📁 Architecture Overview

```
collage-project/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py            # API routes (/analyze, /verify-fix, /compare-scans, /history, /metrics, /settings)
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   └── session.py           # SQLite connection, history & aggregated analytics
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── security.py          # Rate limiting & OWASP security headers
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── analysis.py          # Pydantic models for Explain-Fix-Verify schemas
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── bandit_analyzer.py   # Safe subprocess execution of Bandit AST
│   │   │   ├── coordinator.py       # Orchestrates scans, health scores & fix verification
│   │   │   ├── recommendations.py   # Structured Explain-Fix-Verify knowledge base
│   │   │   ├── ruff_analyzer.py     # Safe subprocess execution of Ruff AST
│   │   │   └── ai_explainer.py      # Optional advisory AI mentor service
│   │   ├── config.py                # Payload limits, rate limits, CORS origins
│   │   └── main.py                  # FastAPI entry point & lifespan events
│   ├── tests/
│   │   ├── test_api.py              # API endpoint, verification, and comparison tests
│   │   ├── test_bandit.py           # Bandit scanner tests
│   │   ├── test_ruff.py             # Ruff linter tests
│   │   └── test_security.py         # Rate limiting, temp file cleanup, and size limits
│   ├── requirements.txt
│   └── codeguard.db                 # Local SQLite database
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CodeEditor.tsx           # Center code editor with line gutter markers
│   │   │   ├── FindingsList.tsx         # Searchable, sortable finding cards
│   │   │   ├── FindingsSummary.tsx      # Health score & metrics banner
│   │   │   ├── FixVerificationPanel.tsx # 5-step Explain. Fix. Verify. inspector
│   │   │   ├── Header.tsx               # Top header with navigation & compare action
│   │   │   ├── WorkspaceSidebar.tsx     # Left collapsible project explorer
│   │   │   ├── ScanComparisonModal.tsx  # Dual-scan comparison dialog
│   │   │   ├── DashboardView.tsx        # Analytics KPIs & grade distribution
│   │   │   ├── HistoryView.tsx          # Searchable SQLite history table
│   │   │   └── SettingsView.tsx         # Engine controls & security limits
│   │   ├── services/
│   │   │   └── api.ts                   # Type-safe API client
│   │   ├── types/
│   │   │   └── index.ts                 # TypeScript interfaces
│   │   ├── App.tsx                      # Main 3-panel workspace coordinator
│   │   └── index.css                    # Design system (charcoal/navy, electric teal)
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── .gitignore
└── README.md
```

---

## ⚡ Quick Start

### 1. Start the FastAPI Backend
```powershell
cd "c:\Users\shashank\OneDrive\Desktop\collage project\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 2. Start the Vite Frontend
```powershell
cd "c:\Users\shashank\OneDrive\Desktop\collage project\frontend"
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Running Automated Tests

### Backend Test Suite (Pytest)
```powershell
cd "c:\Users\shashank\OneDrive\Desktop\collage project\backend"
.\.venv\Scripts\pytest.exe -v
```
*Current test status: 25 passed, 0 failures.*

### Frontend Production Build Test
```powershell
cd "c:\Users\shashank\OneDrive\Desktop\collage project\frontend"
npm run build
```
*Current build status: Clean compilation (`tsc -b && vite build`) in < 1 second.*

---

## 🔒 Security Architecture

1. **Static AST Analysis**: Neither `eval()`, `exec()`, nor shell execution is used on submitted user code.
2. **Subprocess Isolation**: Process arguments are passed as discrete vectors (`['ruff', 'check', ...]` and `['bandit', '-f', 'json', ...]`) with `shell=False`.
3. **Execution Limits**: Configurable timeouts (15s) and payload size caps (100 KB) prevent DoS attacks.
4. **Data Privacy**: Temporary files are erased immediately after scan completion. Only truncated code previews (up to 300 characters) are persisted in local SQLite history.
5. **Disclaimer**: Static analysis detects structural and syntactic vulnerabilities but cannot prove software is 100% defect-free.
