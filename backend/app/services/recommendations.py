"""
CodeGuard AI - Educational Rule Knowledge Base & Fix Templates
==============================================================
Provides structured "Explain. Fix. Verify." content detailing:
1. WHAT WAS DETECTED? - Plain-English summary of the issue
2. WHY DOES IT MATTER? - Realistic risk assessment without exaggeration
3. HOW CAN IT BE IMPROVED? - Practical, actionable remediation advice
4. EXAMPLE OF A SAFER APPROACH - Production-ready safe code pattern
5. HOW CAN I VERIFY THE CHANGE? - Guidance for subsequent verification scans
6. OFFICIAL DOCUMENTATION - Authoritative reference URLs
"""

from typing import Any, Dict, Optional, Tuple

RULE_KNOWLEDGE_BASE: Dict[str, Dict[str, str]] = {
    # -------------------------------------------------------------
    # Bandit Security Rules
    # -------------------------------------------------------------
    "B101": {
        "title": "Assert Used in Production Logic",
        "what_detected": "An `assert` statement was found in non-test application logic.",
        "why_it_matters": (
            "Python's `assert` statement is designed exclusively for testing and internal debugging. "
            "When Python runs with optimization flags (e.g. `python -O`), all assert statements "
            "are completely stripped from bytecode. If you rely on `assert` for permission checks, "
            "authentication, or input validation, the check will be silently bypassed in production."
        ),
        "how_to_improve": (
            "Replace the assert statement with an explicit conditional check that raises an appropriate "
            "exception (such as `ValueError`, `PermissionError`, or custom domain exception)."
        ),
        "safer_example": (
            "# Before (Vulnerable):\n"
            "# assert token is not None, 'Token required'\n\n"
            "# After (Safe):\n"
            "if not token:\n"
            "    raise ValueError('Authentication token is required and cannot be empty')"
        ),
        "verification_guide": "Re-run the scan. Verify that rule B101 is resolved and that unit tests verify the exception is raised.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b101_assert_used.html"
    },
    "B102": {
        "title": "Use of exec() Detected",
        "what_detected": "Dynamic code execution using Python's built-in `exec()` function.",
        "why_it_matters": (
            "`exec()` dynamically parses and executes arbitrary Python code strings within the current process. "
            "If an attacker can manipulate or inject input into the executed string, they gain Remote Code Execution (RCE), "
            "allowing them to read files, steal credentials, or take full control of the host."
        ),
        "how_to_improve": (
            "Avoid dynamic code execution entirely. Replace with explicit function calls, dictionary mapping dispatchers, "
            "or pre-compiled callable tables."
        ),
        "safer_example": (
            "# Before (Vulnerable):\n"
            "# exec(user_submitted_command)\n\n"
            "# After (Safe dispatcher pattern):\n"
            "COMMAND_REGISTRY = {'run': run_task, 'stop': stop_task}\n"
            "handler = COMMAND_REGISTRY.get(command_name)\n"
            "if handler:\n"
            "    handler()\n"
            "else:\n"
            "    raise ValueError(f'Unsupported command: {command_name}')"
        ),
        "verification_guide": "Re-run the scan to verify B102 is cleared. Ensure no user input can influence program instruction flow.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b102_exec_used.html"
    },
    "B104": {
        "title": "Hardcoded Network Bind to 0.0.0.0",
        "what_detected": "Network socket or server configured to bind to all network interfaces (`0.0.0.0`).",
        "why_it_matters": (
            "Binding to `0.0.0.0` exposes the server to all available network interfaces, including public WANs, "
            "internal LANs, and container bridge networks. For development environments or internal APIs, this permits unintended external network access."
        ),
        "how_to_improve": (
            "Bind explicitly to `127.0.0.1` (loopback) for local access, or read the listen interface dynamically from an environment variable."
        ),
        "safer_example": (
            "# Before (Vulnerable):\n"
            "# server.bind(('0.0.0.0', 8080))\n\n"
            "# After (Safe):\n"
            "HOST = os.getenv('APP_BIND_HOST', '127.0.0.1')\n"
            "PORT = int(os.getenv('APP_PORT', '8080'))\n"
            "server.bind((HOST, PORT))"
        ),
        "verification_guide": "Re-scan to ensure B104 is resolved. Verify server only listens on trusted local or configured networks.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b104_hardcoded_bind_all_interfaces.html"
    },
    "B105": {
        "title": "Hardcoded Password String Detected",
        "what_detected": "A hardcoded credential or secret was assigned directly to a variable in the source code.",
        "why_it_matters": (
            "Hardcoded passwords, API keys, and tokens in source files are easily exposed via version control repositories, "
            "build logs, and developer workstations. Once committed to git, credentials remain in repository history forever unless rewritten."
        ),
        "how_to_improve": (
            "Extract credentials into environment variables or use a secret management service (e.g. AWS Secrets Manager, HashiCorp Vault, or a `.env` file)."
        ),
        "safer_example": (
            "# Before (Vulnerable):\n"
            "# DATABASE_PASSWORD = 'super_secret_admin_password_123'\n\n"
            "# After (Safe):\n"
            "import os\n"
            "DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')\n"
            "if not DATABASE_PASSWORD:\n"
            "    raise RuntimeError('DATABASE_PASSWORD environment variable must be configured')"
        ),
        "verification_guide": "Re-run analysis to confirm B105 is resolved. Ensure no plain secret strings remain in source code.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b105_hardcoded_password_string.html"
    },
    "B106": {
        "title": "Hardcoded Password in Function Argument",
        "what_detected": "A hardcoded secret password string passed directly into a function call argument.",
        "why_it_matters": (
            "Hardcoded function arguments reveal secrets in code reviews, logging decorators, and runtime tracebacks."
        ),
        "how_to_improve": "Load the password from a secure configuration object or environment variable.",
        "safer_example": (
            "# Before (Vulnerable):\n"
            "# connect_db(user='admin', password='secretpassword')\n\n"
            "# After (Safe):\n"
            "connect_db(user='admin', password=os.environ['DB_PASSWORD'])"
        ),
        "verification_guide": "Re-scan to verify B106 is eliminated.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b106_hardcoded_password_funcarg.html"
    },
    "B107": {
        "title": "Hardcoded Password in Default Parameter",
        "what_detected": "A hardcoded password string defined as a function parameter default value.",
        "why_it_matters": (
            "Default parameter expressions are evaluated once when Python imports the module. Hardcoded secrets in defaults "
            "permanently attach to the function object in memory and appear in documentation tools."
        ),
        "how_to_improve": "Use `None` as default and read the secret dynamically inside the function body.",
        "safer_example": (
            "# Before (Vulnerable):\n"
            "# def login(token='hardcoded_secret_token_abc'): ...\n\n"
            "# After (Safe):\n"
            "def login(token: Optional[str] = None):\n"
            "    active_token = token or os.getenv('API_TOKEN')\n"
            "    if not active_token:\n"
            "        raise ValueError('No valid API token available')"
        ),
        "verification_guide": "Re-scan to confirm B107 is cleared.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b107_hardcoded_password_default.html"
    },
    "B301": {
        "title": "Insecure Pickle Deserialization",
        "what_detected": "Use of Python's `pickle` serialization format to deserialize untrusted input.",
        "why_it_matters": (
            "Pickle permits serialized objects to define a `__reduce__` method that executes arbitrary system commands "
            "during deserialization. Unpickling data received from untrusted clients directly leads to remote code execution."
        ),
        "how_to_improve": "Use secure data interchange formats such as JSON, Protocol Buffers, or MessagePack.",
        "safer_example": (
            "# Before (Vulnerable):\n"
            "# data = pickle.loads(untrusted_bytes)\n\n"
            "# After (Safe):\n"
            "import json\n"
            "data = json.loads(untrusted_json_string)"
        ),
        "verification_guide": "Re-run scan to verify B301 is resolved. Verify all serialization uses safe parsers.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b301-pickle"
    },
    "B303": {
        "title": "Insecure Hash Function (MD5 / SHA-1)",
        "what_detected": "Use of a cryptographically broken hash algorithm (MD5 or SHA-1).",
        "why_it_matters": (
            "MD5 and SHA-1 suffer from known mathematical collision attacks. Attackers can generate different inputs "
            "that yield the exact same hash, compromising digital signatures, certificate chains, and integrity checks. "
            "Furthermore, neither MD5 nor SHA-1 is suitable for password storage."
        ),
        "how_to_improve": (
            "For general integrity and digest checks, upgrade to SHA-256 (`hashlib.sha256()`). "
            "For password hashing, use dedicated slow key-derivation algorithms like Argon2, bcrypt, or PBKDF2."
        ),
        "safer_example": (
            "# Before (Vulnerable):\n"
            "# token_hash = hashlib.md5(token.encode()).hexdigest()\n\n"
            "# After (Safe cryptographic digest):\n"
            "token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()"
        ),
        "verification_guide": "Re-scan to confirm B303 is resolved. Verify all hash algorithms meet modern security standards.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b303-md5"
    },
    "B307": {
        "title": "Use of eval() Detected",
        "what_detected": "Invocation of Python's dangerous built-in `eval()` function.",
        "why_it_matters": (
            "`eval()` parses and evaluates any input string as arbitrary Python code with the current process permissions. "
            "If an attacker can influence the expression, they can execute system commands, exfiltrate data, or compromise the system."
        ),
        "how_to_improve": (
            "If parsing Python literals (dicts, lists, tuples, numbers), use `ast.literal_eval()`. "
            "For arithmetic or formula evaluation, use a constrained math expression parser."
        ),
        "safer_example": (
            "# Before (Vulnerable):\n"
            "# result = eval(user_expression)\n\n"
            "# After (Safe literal evaluation):\n"
            "import ast\n"
            "try:\n"
            "    result = ast.literal_eval(user_literal_string)\n"
            "except (ValueError, SyntaxError) as exc:\n"
            "    raise ValueError('Invalid literal expression') from exc"
        ),
        "verification_guide": "Re-scan to confirm B307 is resolved. Verify no untrusted strings are evaluated directly.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b307-eval"
    },
    "B324": {
        "title": "Insecure Hashlib Call",
        "what_detected": "Calling legacy or insecure hash algorithms in the `hashlib` library.",
        "why_it_matters": "Using outdated hash functions undermines authentication and integrity verification systems.",
        "how_to_improve": "Use `hashlib.sha256()` or `hashlib.sha3_256()`.",
        "safer_example": (
            "# Before (Vulnerable):\n"
            "# h = hashlib.new('md5')\n\n"
            "# After (Safe):\n"
            "h = hashlib.sha256()"
        ),
        "verification_guide": "Re-scan to confirm B324 is resolved.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b324-hashlib-new-insecure-functions"
    },
    "B403": {
        "title": "Pickle Module Imported",
        "what_detected": "Importing the unsafe Python `pickle` serialization module.",
        "why_it_matters": "Importing `pickle` often leads to insecure deserialization vulnerabilities elsewhere in the application.",
        "how_to_improve": "Use the standard `json` module or safe data serializers instead of pickle.",
        "safer_example": (
            "# Before (Vulnerable):\n"
            "# import pickle\n\n"
            "# After (Safe):\n"
            "import json"
        ),
        "verification_guide": "Re-scan to confirm B403 is resolved.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_imports.html#b403-import-pickle"
    },
    "B602": {
        "title": "Subprocess Call with shell=True",
        "what_detected": "Executing a subprocess command with `shell=True` enabled.",
        "why_it_matters": (
            "When `shell=True` is passed to `subprocess.run` or `subprocess.Popen`, the command string is evaluated by "
            "the system shell (`/bin/sh` or `cmd.exe`). Any unescaped shell metacharacters (`;`, `&`, `|`, `$`) allow an attacker "
            "to chain and execute arbitrary shell commands."
        ),
        "how_to_improve": (
            "Set `shell=False` (the default) and pass command arguments strictly as a list of strings."
        ),
        "safer_example": (
            "# Before (Vulnerable):\n"
            "# subprocess.run(f'ping -c 1 {user_ip}', shell=True)\n\n"
            "# After (Safe):\n"
            "subprocess.run(['ping', '-c', '1', user_ip], shell=False, check=True)"
        ),
        "verification_guide": "Re-scan to verify B602 is cleared. Ensure no arguments can trigger shell expansion.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b602_subprocess_popen_with_shell_equals_true.html"
    },
    "B603": {
        "title": "Subprocess Call Without Shell Protection",
        "what_detected": "Subprocess launched without an allowlist check on command arguments.",
        "why_it_matters": "Even without shell=True, user-controlled argument vectors can trigger dangerous program flags.",
        "how_to_improve": "Validate all command parameters against a strict allowlist before invoking subprocess.",
        "safer_example": (
            "# Before (Potential flaw):\n"
            "# subprocess.run(['git', user_flag])\n\n"
            "# After (Safe with allowlist validation):\n"
            "ALLOWED_FLAGS = {'--stat', '--summary'}\n"
            "if user_flag not in ALLOWED_FLAGS:\n"
            "    raise ValueError('Disallowed command flag')\n"
            "subprocess.run(['git', 'diff', user_flag], check=True)"
        ),
        "verification_guide": "Re-scan to ensure B603 is resolved.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b603_subprocess_without_shell_equals_true.html"
    },
    "B608": {
        "title": "Potential SQL Injection",
        "what_detected": "SQL statement constructed dynamically using string concatenation, f-strings, or `%` formatting.",
        "why_it_matters": (
            "Formatting SQL queries via string interpolation allows attackers to break out of data literals and inject raw SQL syntax. "
            "This permits unauthorized authentication bypass, complete database exfiltration, or table modification."
        ),
        "how_to_improve": (
            "Always use parameterized queries (prepared statements). Pass user input as separate tuple parameters to the database driver."
        ),
        "safer_example": (
            "# Before (Vulnerable SQL Injection):\n"
            "# query = f'SELECT * FROM users WHERE id = {user_input_id}'\n"
            "# cursor.execute(query)\n\n"
            "# After (Safe Parameterized Query):\n"
            "query = 'SELECT * FROM users WHERE id = ?'\n"
            "cursor.execute(query, (user_input_id,))"
        ),
        "verification_guide": "Re-run scan. Verify that rule B608 is resolved and SQL queries use driver parameter binding.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b608_hardcoded_sql_expressions.html"
    },

    # -------------------------------------------------------------
    # Ruff Quality, Syntax & PEP 8 Rules
    # -------------------------------------------------------------
    "F401": {
        "title": "Unused Import",
        "what_detected": "A module or symbol was imported but never referenced in the file.",
        "why_it_matters": (
            "Unused imports unnecessarily increase startup time, consume memory, pollute namespace scopes, and "
            "obscure genuine project dependencies."
        ),
        "how_to_improve": "Remove the unused import statement from the file.",
        "safer_example": (
            "# Before:\n"
            "# import os\n"
            "# import sys  # sys is never used in this file\n\n"
            "# After:\n"
            "import os"
        ),
        "verification_guide": "Re-scan to verify F401 is resolved.",
        "docs": "https://docs.astral.sh/ruff/rules/unused-import/"
    },
    "F841": {
        "title": "Unused Local Variable",
        "what_detected": "A variable was assigned a value but never read anywhere in the scope.",
        "why_it_matters": (
            "Unused variables frequently point to programming oversights (such as calculating a result and forgetting to return it) "
            "or dead code that burdens maintainability."
        ),
        "how_to_improve": (
            "Either utilize the variable, delete the unused assignment, or prefix with an underscore (`_`) if required by an API contract."
        ),
        "safer_example": (
            "# Before:\n"
            "# total_tax = calculate_tax(price)\n"
            "# return price\n\n"
            "# After:\n"
            "total_tax = calculate_tax(price)\n"
            "return price + total_tax"
        ),
        "verification_guide": "Re-scan to verify F841 is cleared.",
        "docs": "https://docs.astral.sh/ruff/rules/unused-variable/"
    },
    "F821": {
        "title": "Undefined Name",
        "what_detected": "A variable or function name is referenced without being defined or imported.",
        "why_it_matters": (
            "Accessing an undefined symbol will trigger a runtime `NameError` crash as soon as that execution branch is reached."
        ),
        "how_to_improve": "Define the variable or import the required symbol before referencing it.",
        "safer_example": (
            "# Before:\n"
            "# def run():\n"
            "#     return missing_var + 10\n\n"
            "# After:\n"
            "def run(missing_var: int = 0) -> int:\n"
            "    return missing_var + 10"
        ),
        "verification_guide": "Re-scan to ensure F821 is resolved.",
        "docs": "https://docs.astral.sh/ruff/rules/undefined-variable/"
    },
    "E711": {
        "title": "Comparison to None Using Equality Operator",
        "what_detected": "Comparison to `None` using `== None` or `!= None` instead of identity operators.",
        "why_it_matters": (
            "In Python, `None` is a singleton. The equality operator `==` invokes the object's `__eq__` method, which can "
            "be overridden to return misleading results. Using identity checks (`is` / `is not`) is faster and avoids side effects."
        ),
        "how_to_improve": "Use `if val is None:` or `if val is not None:`.",
        "safer_example": (
            "# Before:\n"
            "# if data == None: ...\n\n"
            "# After:\n"
            "if data is None: ..."
        ),
        "verification_guide": "Re-scan to verify E711 is resolved.",
        "docs": "https://docs.astral.sh/ruff/rules/none-comparison/"
    },
    "E712": {
        "title": "Comparison to True/False Using Equality Operator",
        "what_detected": "Comparison to a boolean using `== True` or `== False`.",
        "why_it_matters": "Direct boolean comparisons violate PEP 8 conventions and can lead to bugs with custom truthy objects.",
        "how_to_improve": "Write `if is_active:` or `if not is_active:`.",
        "safer_example": (
            "# Before:\n"
            "# if user.is_active == True: ...\n\n"
            "# After:\n"
            "if user.is_active: ..."
        ),
        "verification_guide": "Re-scan to verify E712 is resolved.",
        "docs": "https://docs.astral.sh/ruff/rules/true-false-comparison/"
    },
    "E722": {
        "title": "Bare Exception Handling",
        "what_detected": "A bare `except:` clause without an explicit exception class.",
        "why_it_matters": (
            "A bare `except:` catches all exceptions, including `KeyboardInterrupt` (Ctrl+C) and `SystemExit`, preventing clean program "
            "termination and concealing serious syntax or typing bugs."
        ),
        "how_to_improve": "Specify the exact expected exception classes (e.g. `except (ValueError, KeyError):`) or at least `except Exception:`.",
        "safer_example": (
            "# Before:\n"
            "# try:\n"
            "#     val = int(text)\n"
            "# except:\n"
            "#     val = 0\n\n"
            "# After:\n"
            "try:\n"
            "    val = int(text)\n"
            "except ValueError:\n"
            "    val = 0"
        ),
        "verification_guide": "Re-scan to verify E722 is resolved.",
        "docs": "https://docs.astral.sh/ruff/rules/bare-except/"
    },
    "B006": {
        "title": "Mutable Default Argument in Function Definition",
        "what_detected": "A mutable data structure (such as a list `[]` or dict `{}`) used as a default argument value.",
        "why_it_matters": (
            "Python evaluates default argument values once at function definition time, not on each invocation. "
            "Modifying a mutable default leaks state across separate function calls, producing subtle, hard-to-reproduce bugs."
        ),
        "how_to_improve": "Use `None` as the default argument value and initialize the mutable object inside the function body.",
        "safer_example": (
            "# Before (Buggy state leak):\n"
            "# def append_item(item, items=[]):\n"
            "#     items.append(item)\n"
            "#     return items\n\n"
            "# After (Safe idempotent function):\n"
            "from typing import Optional, List\n\n"
            "def append_item(item: int, items: Optional[List[int]] = None) -> List[int]:\n"
            "    if items is None:\n"
            "        items = []\n"
            "    items.append(item)\n"
            "    return items"
        ),
        "verification_guide": "Re-scan to confirm B006 is resolved. Verify function calls produce independent list instances.",
        "docs": "https://docs.astral.sh/ruff/rules/mutable-argument-default/"
    },
    "E501": {
        "title": "Line Too Long",
        "what_detected": "Source code line exceeds the configured maximum line length.",
        "why_it_matters": "Excessively long lines reduce readability on split-screen editors and code review tools.",
        "how_to_improve": "Split the line across multiple lines using parentheses or intermediate helper variables.",
        "safer_example": (
            "# Before:\n"
            "# query = 'SELECT id, username, email, full_name, created_at, updated_at FROM active_users WHERE status = \"active\" ORDER BY id DESC'\n\n"
            "# After:\n"
            "query = (\n"
            "    'SELECT id, username, email, full_name, created_at, updated_at '\n"
            "    'FROM active_users '\n"
            "    'WHERE status = \"active\" '\n"
            "    'ORDER BY id DESC'\n"
            ")"
        ),
        "verification_guide": "Re-scan to verify E501 is resolved.",
        "docs": "https://docs.astral.sh/ruff/rules/line-too-long/"
    },
    "W291": {
        "title": "Trailing Whitespace",
        "what_detected": "Unnecessary space or tab characters at the end of a line.",
        "why_it_matters": "Trailing whitespace adds visual clutter and creates noisy, confusing git diffs in pull requests.",
        "how_to_improve": "Delete trailing spaces from the end of the line.",
        "safer_example": (
            "# Before: line contains spaces at end\n"
            "# def foo():    \n\n"
            "# After: cleanly trimmed\n"
            "# def foo():"
        ),
        "verification_guide": "Re-scan to verify W291 is resolved.",
        "docs": "https://docs.astral.sh/ruff/rules/trailing-whitespace/"
    },
    "W293": {
        "title": "Blank Line Contains Whitespace",
        "what_detected": "An empty line contains whitespace characters (spaces or tabs).",
        "why_it_matters": "Blank lines containing whitespace pollute source files and violate PEP 8 standards.",
        "how_to_improve": "Clear all whitespace characters from empty lines.",
        "safer_example": "# Remove all invisible space characters from blank lines.",
        "verification_guide": "Re-scan to verify W293 is resolved.",
        "docs": "https://docs.astral.sh/ruff/rules/blank-line-contains-whitespace/"
    }
}


def get_rule_details_structured(
    rule_id: str,
    default_message: str = "",
    filename: str = "submission.py",
    line: Optional[int] = None
) -> Dict[str, Optional[str]]:
    """
    Returns the comprehensive 6-part "Explain. Fix. Verify." data structure for a finding.
    """
    rule_upper = rule_id.upper()
    info = RULE_KNOWLEDGE_BASE.get(rule_upper)

    where_text = f"{filename} (Line {line})" if line else filename

    if info:
        return {
            "what_detected": info.get("what_detected") or default_message or info.get("title", "Issue detected"),
            "why_it_matters": info.get("why_it_matters"),
            "where_is_it": where_text,
            "how_to_improve": info.get("how_to_improve") or info.get("recommendation"),
            "safer_example": info.get("safer_example"),
            "verification_guide": info.get("verification_guide") or "Re-scan the code to verify this rule is no longer reported.",
            "docs": info.get("docs")
        }

    # Heuristic fallback for rules not explicitly registered in dictionary
    prefix = rule_upper[0] if rule_upper else ""
    if prefix == "B" and len(rule_upper) > 1 and rule_upper[1].isdigit():
        what = f"Security vulnerability flagged by Bandit: {default_message or rule_id}"
        why = "Potential security vulnerability detected via static AST inspection. Untrusted input or insecure patterns may lead to system compromise."
        improve = f"Review the implementation of {rule_id} and replace with secure alternatives or parameterized queries."
        safer = "# Replace dynamic or insecure construction with typed, parameterized alternatives."
        docs = "https://bandit.readthedocs.io/"
    elif prefix == "F":
        what = f"Code quality defect flagged by Pyflakes: {default_message or rule_id}"
        why = "Undefined variables, unused imports, or duplicate definitions can lead to runtime crashes or maintainability issues."
        improve = f"Verify definitions and imports for rule {rule_id}."
        safer = "# Clean up definitions and ensure all referenced symbols are defined."
        docs = "https://docs.astral.sh/ruff/rules/"
    elif prefix in ("E", "W"):
        what = f"PEP 8 formatting or style issue: {default_message or rule_id}"
        why = "Inconsistent styling and conventions reduce readability across engineering teams."
        improve = f"Format code according to PEP 8 standards ({rule_id})."
        safer = "# Format line lengths, indentation, and trailing spaces according to PEP 8."
        docs = "https://docs.astral.sh/ruff/rules/"
    else:
        what = default_message or f"Static inspection finding {rule_id}"
        why = "Static analysis detected a code pattern that deviates from recommended best practices."
        improve = "Review the flagged code and apply Python standard practices."
        safer = None
        docs = None

    return {
        "what_detected": what,
        "why_it_matters": why,
        "where_is_it": where_text,
        "how_to_improve": improve,
        "safer_example": safer,
        "verification_guide": "Re-run static analysis to confirm this finding is resolved.",
        "docs": docs
    }


def get_rule_details(rule_id: str, default_message: str = "") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Backward-compatible 3-tuple return for older services:
    (why_it_matters, recommendation, docs)
    """
    structured = get_rule_details_structured(rule_id, default_message)
    return (
        structured["why_it_matters"],
        structured["how_to_improve"],
        structured["docs"]
    )


def get_recommendation_for_rule(rule_id: str, default_message: str = "") -> Optional[str]:
    """Backward-compatible helper returning recommendation string."""
    _, rec, _ = get_rule_details(rule_id, default_message)
    return rec


def get_docs_for_rule(rule_id: str) -> Optional[str]:
    """Backward-compatible helper returning docs URL string."""
    _, _, docs = get_rule_details(rule_id)
    return docs
