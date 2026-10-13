# CodeGuard AI 🛡️

**AI-Powered Python Code Review & Security Analysis Platform**

CodeGuard AI is a full-stack developer tool designed to analyze Python source code for security vulnerabilities, software defects, and style anti-patterns using industry-grade static analysis tools (**Bandit** and **Ruff**).

---

## 🚀 Key Features

1. **Modern Developer Dashboard**: Dark-mode developer interface with responsive layouts, accessible contrast, and high-visibility status indicators.
2. **Interactive Code Editor**: Line numbers, code size indicator, keyboard shortcuts (`Ctrl+Enter`), and sample code loaders.
3. **Dual Static Analysis Engine**:
   - **Bandit**: AST-based security vulnerability detection (hardcoded credentials, SQL injection vectors, dangerous `eval`/`exec`, insecure cryptographic algorithms like MD5).
   - **Ruff**: Lightning-fast Rust-powered linter for code quality, unused variables/imports (`F401`), syntax errors, and PEP-8 conventions.
4. **Actionable Findings & Recommendations**: Each issue includes rule codes, severity badges, offending code snippets, and beginner-friendly mentor remediations.
5. **Code Health Scoring**: Computes an overall score (0–100) and letter grade (A–F) based on issue severity deductions.
6. **Local Persistence**: Saves analysis runs in SQLite with a built-in History Viewer.
7. **One-Click Samples**: Instantly switch between vulnerable and clean sample code.
8. **Safe by Design**: Analyzes code using static Abstract Syntax Trees (AST). User code is **never executed** on the server.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Vanilla CSS |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2 |
| **Security Scanner** | Bandit (`bandit -f json`) |
| **Quality & Linter** | Ruff (`ruff check --output-format json`) |
| **Database** | SQLite (built-in `sqlite3`) |
| **Testing** | Pytest, HTTPX |

---

## 📁 Project Architecture

```
collage-project/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py            # API endpoints (/analyze, /history, /samples, /health)
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   └── session.py           # SQLite connection & scan history persistence
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── analysis.py          # Pydantic models for validation & serialization
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── bandit_analyzer.py   # Safe subprocess execution of Bandit
│   │   │   ├── coordinator.py       # Orchestrates scans, scores & metrics
│   │   │   ├── recommendations.py   # Educational knowledge base for rules
│   │   │   └── ruff_analyzer.py     # Safe subprocess execution of Ruff
│   │   ├── config.py                # Payload limits, tool paths, CORS
│   │   └── main.py                  # FastAPI application entrypoint
│   ├── tests/
│   │   ├── test_api.py              # API endpoint integration tests
│   │   ├── test_bandit.py           # Bandit scanner unit tests
│   │   └── test_ruff.py             # Ruff linter unit tests
│   └── requirements.txt             # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CodeEditor.tsx       # Textarea with synchronized line numbers
│   │   │   ├── FindingsList.tsx     # Filterable finding cards & snippets
│   │   │   ├── FindingsSummary.tsx  # Health grade & metrics overview
│   │   │   ├── Header.tsx           # Status badge & navigation header
│   │   │   └── ScanHistoryModal.tsx # SQLite scan history dialog
│   │   ├── services/
│   │   │   └── api.ts               # Fetch client communicating with backend
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript interfaces
│   │   ├── App.tsx                  # Main layout container
│   │   ├── index.css                # Polished developer theme styles
│   │   └── main.tsx                 # React DOM mount point
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts               # Dev server & API proxy configuration
│
├── .gitignore                       # Ignores .venv, node_modules, and cache files
└── README.md
```

---

## ⚡ Quick Start (Windows)

### 1. Clone & Enter Directory
```powershell
git clone https://github.com/Shashank-kc/collage-project.git
cd collage-project
```

### 2. Set Up the Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run tests to ensure everything is configured properly:
```powershell
pytest -v
```

Start the backend API server:
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Set Up the Frontend (In a New Terminal)
```powershell
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🔒 Security & Safe Execution Notice

- **No Code Execution**: Submitted Python code is strictly parsed by static analyzers as an Abstract Syntax Tree (AST) inside an isolated temporary directory. It is **never** imported, executed (`eval`/`exec`), or run directly.
- **Payload Limits**: Requests exceeding 100 KB are rejected to prevent denial-of-service (DoS) attempts.
- **Subprocess Isolation**: Analysis subprocesses run with strict timeouts (15 seconds) to prevent hanging.

---

## ⚠️ Known Limitations & Disclaimer

- **Static Analysis vs. Runtime Bugs**: Static analysis tools inspect structure and syntax; they cannot detect runtime state defects, complex algorithmic mistakes, or external service failures.
- **Tool-Generated Results**: Findings are tool-generated indicators and should be treated as guidance, not formal verification guarantees.

---

## 👨‍💻 Author & Acknowledgements
- Built as an AI/ML Computer Science engineering project.
- Powered by [FastAPI](https://fastapi.tiangolo.com/), [Ruff](https://docs.astral.sh/ruff/), [Bandit](https://bandit.readthedocs.io/), and [React](https://react.dev/).
