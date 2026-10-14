"""
CodeGuard AI - Educational Rule Knowledge Base
==============================================
Provides beginner-friendly, mentor-style explanations detailing:
1. What the finding is
2. Why the issue matters (security / architectural risk)
3. Actionable remediation (concrete fix)
4. Official documentation reference
"""

from typing import Dict, Optional, Tuple

RULE_KNOWLEDGE_BASE: Dict[str, Dict[str, str]] = {
    # Bandit Security Rules
    "B101": {
        "title": "Assert Used in Production Logic",
        "why_it_matters": (
            "Python's `assert` statement is designed exclusively for testing and debugging. "
            "When Python runs with optimization flags (e.g., `python -O`), all assert statements "
            "are completely stripped from bytecode. If you rely on `assert` for authentication, "
            "input authorization, or permission checking, the check will be silently bypassed in production."
        ),
        "recommendation": "Use explicit condition checks: `if not condition: raise ValueError('Invalid input')`.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b101_assert_used.html"
    },
    "B102": {
        "title": "Use of exec() Detected",
        "why_it_matters": (
            "`exec()` dynamically parses and executes arbitrary Python code within the current process scope. "
            "If an attacker can manipulate or inject input into the executed string, they gain Remote Code Execution (RCE), "
            "allowing them to read files, steal credentials, or compromise the server."
        ),
        "recommendation": "Avoid dynamic code execution. Refactor with direct function calls, mapping dictionaries, or static dispatch tables.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b102_exec_used.html"
    },
    "B104": {
        "title": "Hardcoded Network Bind to 0.0.0.0",
        "why_it_matters": (
            "Binding a network service to `0.0.0.0` exposes it on all available network interfaces (including public IP addresses, "
            "internal LANs, and Docker bridges). For local development or internal microservices, this permits unintended external network access."
        ),
        "recommendation": "Bind explicitly to `127.0.0.1` for loopback localhost access, or configure the host via an environment variable.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b104_hardcoded_bind_all_interfaces.html"
    },
    "B105": {
        "title": "Hardcoded Password String Detected",
        "why_it_matters": (
            "Hardcoding credentials directly in source files risks leaking secrets into version control (git), "
            "CI/CD logs, and client bundles. Once committed, credentials remain in git history even after deletion."
        ),
        "recommendation": "Store credentials in environment variables (`os.getenv('DB_PASSWORD')`) or use a `.env` file managed with `python-dotenv`.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b105_hardcoded_password_string.html"
    },
    "B106": {
        "title": "Hardcoded Password in Function Argument",
        "why_it_matters": (
            "Passing hardcoded secret strings as arguments exposes sensitive tokens in stack traces, error reports, and code reviews."
        ),
        "recommendation": "Pass credentials dynamically from a secure vault or runtime configuration.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b106_hardcoded_password_funcarg.html"
    },
    "B107": {
        "title": "Hardcoded Password in Default Argument",
        "why_it_matters": (
            "Default argument expressions are evaluated once when Python imports the module. Storing secrets here binds "
            "them permanently to the function object in memory."
        ),
        "recommendation": "Use `None` as the default argument value and read the secret inside the function body.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b107_hardcoded_password_default.html"
    },
    "B301": {
        "title": "Insecure Pickle Deserialization",
        "why_it_matters": (
            "Python's `pickle` library allows serialized objects to define a `__reduce__` method that executes arbitrary "
            "system commands during deserialization. Loading untrusted pickle files directly triggers remote code execution."
        ),
        "recommendation": "Never unpickle data from untrusted clients. Use safe serialization formats like JSON (`json.loads`) or Protocol Buffers.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b301-pickle"
    },
    "B303": {
        "title": "Insecure Hash Function (MD5 / SHA-1)",
        "why_it_matters": (
            "MD5 and SHA-1 have known mathematical collision vulnerabilities and can be forged or inverted rapidly using modern GPUs or rainbow tables."
        ),
        "recommendation": "Use cryptographically robust hashes: `hashlib.sha256()` or `hashlib.sha3_256()`. For passwords, use Argon2 or bcrypt.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b303-md5"
    },
    "B307": {
        "title": "Use of eval() Detected",
        "why_it_matters": (
            "`eval()` interprets any string as Python code with the caller's privileges. If untrusted input enters `eval`, "
            "an attacker can run malicious code, exfiltrate data, or erase files."
        ),
        "recommendation": "If parsing simple data structures, use `ast.literal_eval()`. For math formulas, use dedicated expression parsers.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b307-eval"
    },
    "B324": {
        "title": "Insecure Hashlib Call",
        "why_it_matters": (
            "Calling legacy hash algorithms in `hashlib` weakens authentication and digital signature verification."
        ),
        "recommendation": "Upgrade to SHA-256 (`hashlib.sha256()`) or stronger hash suites.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b324-hashlib-new-insecure-functions"
    },
    "B403": {
        "title": "Pickle Module Imported",
        "why_it_matters": (
            "Importing `pickle` often leads to insecure deserialization patterns later in the codebase."
        ),
        "recommendation": "Prefer the standard `json` library or `yaml.safe_load` for safe data exchange.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_imports.html#b403-import-pickle"
    },
    "B602": {
        "title": "Subprocess Call with shell=True",
        "why_it_matters": (
            "When `shell=True` is passed to `subprocess.Popen` or `subprocess.run`, the command is executed via the system shell (`/bin/sh` or `cmd.exe`). "
            "Any unsanitized metacharacters (`;`, `&`, `|`, `` ` ``) enable Command Injection."
        ),
        "recommendation": "Set `shell=False` and pass arguments as a list: `subprocess.run(['command', 'arg1', 'arg2'])`.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b602_subprocess_popen_with_shell_equals_true.html"
    },
    "B603": {
        "title": "Subprocess Call Without Shell Protection",
        "why_it_matters": (
            "Executing subprocesses without strict validation of arguments may allow unexpected command execution if inputs are partially user-controlled."
        ),
        "recommendation": "Ensure all arguments passed to `subprocess.run` are strictly type-checked and validated against an allowlist.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b603_subprocess_without_shell_equals_true.html"
    },
    "B608": {
        "title": "Potential SQL Injection",
        "why_it_matters": (
            "Constructing SQL statements via string formatting (`f'...'`, `%`, or `+`) allows attackers to inject arbitrary SQL syntax, "
            "bypassing authentication, dumping entire databases, or modifying data."
        ),
        "recommendation": "Always use parameterized queries: `cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))`.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b608_hardcoded_sql_expressions.html"
    },

    # Ruff Quality & Style Rules
    "F401": {
        "title": "Unused Import",
        "why_it_matters": (
            "Unused imports pollute the namespace, slow down application startup, consume unnecessary memory, and create confusion about module dependencies."
        ),
        "recommendation": "Remove the unused import from the file.",
        "docs": "https://docs.astral.sh/ruff/rules/unused-import/"
    },
    "F841": {
        "title": "Unused Local Variable",
        "why_it_matters": (
            "A variable assigned but never read indicates either dead code or an intended calculation whose result was accidentally forgotten."
        ),
        "recommendation": "Either use the variable in subsequent logic, delete it, or prefix with an underscore (`_`) if required by an interface.",
        "docs": "https://docs.astral.sh/ruff/rules/unused-variable/"
    },
    "F821": {
        "title": "Undefined Name",
        "why_it_matters": (
            "Referencing an undefined variable or function causes a `NameError` crash at runtime when that branch executes."
        ),
        "recommendation": "Check for typos or import the required symbol before using it.",
        "docs": "https://docs.astral.sh/ruff/rules/undefined-variable/"
    },
    "E711": {
        "title": "Comparison to None Using Equality Operator",
        "why_it_matters": (
            "Using `== None` invokes the object's `__eq__` method, which can be overridden or return unexpected results. In Python, `None` is a singleton."
        ),
        "recommendation": "Use identity testing: `if x is None:` or `if x is not None:`.",
        "docs": "https://docs.astral.sh/ruff/rules/none-comparison/"
    },
    "E712": {
        "title": "Comparison to True/False Using Equality Operator",
        "why_it_matters": (
            "Writing `if flag == True:` is unpythonic and prone to truthiness misunderstandings."
        ),
        "recommendation": "Write `if flag:` or `if not flag:` directly.",
        "docs": "https://docs.astral.sh/ruff/rules/true-false-comparison/"
    },
    "E722": {
        "title": "Bare Exception Handling",
        "why_it_matters": (
            "A bare `except:` catches all exceptions, including `KeyboardInterrupt` (Ctrl+C) and `SystemExit`, preventing the program from terminating cleanly "
            "and masking critical programming bugs."
        ),
        "recommendation": "Catch specific exceptions: `except (ValueError, KeyError):` or at minimum `except Exception:`.",
        "docs": "https://docs.astral.sh/ruff/rules/bare-except/"
    },
    "B006": {
        "title": "Mutable Default Argument in Function Definition",
        "why_it_matters": (
            "Python evaluates default function arguments once when the function is defined. If the default is mutable (e.g. `[]` or `{}`), "
            "every function call shares and mutates the exact same instance across calls, causing bizarre state leaks."
        ),
        "recommendation": "Use `None` as default: `def append_item(val, items=None): if items is None: items = []`.",
        "docs": "https://docs.astral.sh/ruff/rules/mutable-argument-default/"
    },
    "E501": {
        "title": "Line Too Long",
        "why_it_matters": (
            "Overly long lines reduce code readability on split-screen editors and code review tools."
        ),
        "recommendation": "Break the line across multiple lines using parentheses or intermediate variables.",
        "docs": "https://docs.astral.sh/ruff/rules/line-too-long/"
    },
    "W291": {
        "title": "Trailing Whitespace",
        "why_it_matters": (
            "Trailing whitespace creates noisy git diffs and violates PEP 8 formatting standards."
        ),
        "recommendation": "Strip whitespace characters from the end of the line.",
        "docs": "https://docs.astral.sh/ruff/rules/trailing-whitespace/"
    },
    "W293": {
        "title": "Blank Line Contains Whitespace",
        "why_it_matters": (
            "Blank lines with whitespace create invisible clutter in source files."
        ),
        "recommendation": "Delete spaces/tabs from empty lines.",
        "docs": "https://docs.astral.sh/ruff/rules/blank-line-contains-whitespace/"
    }
}


def get_rule_details(rule_id: str, default_message: str = "") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Returns (why_it_matters, recommendation, documentation_url) for a rule.
    """
    rule_upper = rule_id.upper()
    info = RULE_KNOWLEDGE_BASE.get(rule_upper)
    if info:
        return (info["why_it_matters"], info["recommendation"], info["docs"])

    # Fallback heuristic
    prefix = rule_upper[0] if rule_upper else ""
    if prefix == "B" and len(rule_upper) > 1 and rule_upper[1].isdigit():
        why = "Potential security risk detected by Bandit. Insecure coding practices can permit data leaks or system manipulation."
        rec = f"Review the implementation of {rule_id} and replace with secure alternatives or parameterized queries."
        docs = "https://bandit.readthedocs.io/"
    elif prefix == "F":
        why = "Code quality or potential runtime error flagged by Pyflakes. Undefined or unused symbols complicate maintenance."
        rec = f"Verify definitions and imports for rule {rule_id}."
        docs = "https://docs.astral.sh/ruff/rules/"
    elif prefix in ("E", "W"):
        why = "PEP 8 style convention issue. Inconsistent styling reduces readability across teams."
        rec = f"Format code according to PEP 8 standards ({rule_id})."
        docs = "https://docs.astral.sh/ruff/rules/"
    else:
        why = "Code inspection finding detected during static analysis."
        rec = "Review the flagged code and apply Python best practices."
        docs = None

    return (why, rec, docs)


def get_recommendation_for_rule(rule_id: str, default_message: str = "") -> Optional[str]:
    """Backward-compatible helper returning recommendation string."""
    _, rec, _ = get_rule_details(rule_id, default_message)
    return rec


def get_docs_for_rule(rule_id: str) -> Optional[str]:
    """Backward-compatible helper returning docs URL string."""
    _, _, docs = get_rule_details(rule_id)
    return docs

