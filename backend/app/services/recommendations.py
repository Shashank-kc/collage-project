"""
CodeGuard AI - Educational Rule Knowledge Base
==============================================
Provides beginner-friendly, mentor-style explanations and remediations
for common Python static analysis findings (Bandit and Ruff).
"""

from typing import Dict, Optional

# Knowledge base of rule explanations and actionable recommendations
RULE_KNOWLEDGE_BASE: Dict[str, Dict[str, str]] = {
    # Bandit Security Rules
    "B101": {
        "title": "Assert Used in Production Logic",
        "recommendation": "Assert statements are removed when Python runs with optimization flags (python -O). Use explicit validation: 'if not condition: raise ValueError(...)'.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b101_assert_used.html"
    },
    "B102": {
        "title": "Use of exec() Detected",
        "recommendation": "exec() dynamically runs arbitrary Python code. If untrusted input reaches exec, attackers gain full code execution. Refactor using standard functions or dispatch tables.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b102_exec_used.html"
    },
    "B104": {
        "title": "Hardcoded Network Bind to 0.0.0.0",
        "recommendation": "Binding to '0.0.0.0' exposes your application on all network interfaces. For local development or internal services, bind to '127.0.0.1' or configure host via an environment variable.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b104_hardcoded_bind_all_interfaces.html"
    },
    "B105": {
        "title": "Hardcoded Password String Detected",
        "recommendation": "Hardcoding credentials exposes sensitive passwords in source control. Load secrets from environment variables using `os.getenv('PASSWORD')` or a `.env` file with `python-dotenv`.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b105_hardcoded_password_string.html"
    },
    "B106": {
        "title": "Hardcoded Password in Function Argument",
        "recommendation": "Do not pass passwords or API keys as default function parameters. Read credentials dynamically at runtime.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b106_hardcoded_password_funcarg.html"
    },
    "B107": {
        "title": "Hardcoded Password in Default Argument",
        "recommendation": "Do not use secrets as default parameter values. Default arguments are evaluated at function definition time.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b107_hardcoded_password_default.html"
    },
    "B301": {
        "title": "Insecure Pickle Deserialization",
        "recommendation": "Pickle can execute arbitrary code during deserialization (__reduce__ method). Never unpickle data received from untrusted clients. Use JSON, Protocol Buffers, or MessagePack.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b301-pickle"
    },
    "B303": {
        "title": "Insecure Hash Function (MD5 / SHA-1)",
        "recommendation": "MD5 and SHA-1 have known collision vulnerabilities. Use modern cryptographic hash functions like SHA-256 (`hashlib.sha256()`) or SHA-3.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b303-md5"
    },
    "B307": {
        "title": "Use of eval() Detected",
        "recommendation": "eval() executes any string as Python code, enabling remote code execution. If you need to parse simple literals, use `ast.literal_eval()`. Otherwise, use `json.loads()`.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b307-eval"
    },
    "B324": {
        "title": "Insecure Hashlib Call",
        "recommendation": "Weak hashing algorithm used. For passwords, use Argon2 or bcrypt. For data integrity, use SHA-256 or SHA-512.",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b324-hashlib-new-insecure-functions"
    },
    "B403": {
        "title": "Pickle Module Imported",
        "recommendation": "Consider replacing pickle with a safer serialization format such as JSON or safe YAML loaders (`yaml.safe_load`).",
        "docs": "https://bandit.readthedocs.io/en/latest/blacklists/blacklist_imports.html#b403-import-pickle"
    },
    "B602": {
        "title": "Subprocess Call with shell=True",
        "recommendation": "Passing `shell=True` to subprocess allows shell injection if input contains metacharacters like `;`, `&`, or `|`. Set `shell=False` and pass arguments as a list: `['ls', '-l']`.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b602_subprocess_popen_with_shell_equals_true.html"
    },
    "B603": {
        "title": "Subprocess Call Without Shell Protection",
        "recommendation": "Ensure all arguments passed to `subprocess.run` or `Popen` are strictly validated and sanitized before execution.",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b603_subprocess_without_shell_equals_true.html"
    },
    "B608": {
        "title": "Potential SQL Injection",
        "recommendation": "Building SQL queries with f-strings, `%`, or `+` concatenation allows attackers to manipulate SQL syntax. Always use parameterized queries (e.g., `cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))`).",
        "docs": "https://bandit.readthedocs.io/en/latest/plugins/b608_hardcoded_sql_expressions.html"
    },

    # Ruff Quality & Style Rules
    "F401": {
        "title": "Unused Import",
        "recommendation": "The imported module or symbol is never referenced in this file. Remove it to keep imports clean and reduce startup overhead.",
        "docs": "https://docs.astral.sh/ruff/rules/unused-import/"
    },
    "F841": {
        "title": "Unused Local Variable",
        "recommendation": "Variable assigned but never read. Either remove it, use it in subsequent calculations, or prefix it with an underscore `_var` if intentionally unused.",
        "docs": "https://docs.astral.sh/ruff/rules/unused-variable/"
    },
    "F821": {
        "title": "Undefined Name",
        "recommendation": "The variable, function, or class name is referenced before being defined or imported. Check for typos or missing import statements.",
        "docs": "https://docs.astral.sh/ruff/rules/undefined-variable/"
    },
    "E711": {
        "title": "Comparison to None Using Equality Operator",
        "recommendation": "Use `if x is None:` or `if x is not None:` instead of `== None`. In Python, `is` tests identity and is both faster and safe against custom `__eq__` methods.",
        "docs": "https://docs.astral.sh/ruff/rules/none-comparison/"
    },
    "E712": {
        "title": "Comparison to True/False Using Equality Operator",
        "recommendation": "Use `if cond:` or `if not cond:` rather than `if cond == True:`. It is cleaner and follows Python PEP 8 style standards.",
        "docs": "https://docs.astral.sh/ruff/rules/true-false-comparison/"
    },
    "E722": {
        "title": "Bare Exception Handling",
        "recommendation": "Using `except:` catches everything, including KeyboardInterrupt (Ctrl+C) and SystemExit. Always catch specific exceptions, e.g., `except (ValueError, KeyError):` or at minimum `except Exception:`.",
        "docs": "https://docs.astral.sh/ruff/rules/bare-except/"
    },
    "B006": {
        "title": "Mutable Default Argument in Function Definition",
        "recommendation": "In Python, default arguments are created once when the function is defined. Passing a mutable default like `def foo(items=[])` shares that list across all function calls! Use `def foo(items=None): if items is None: items = []`.",
        "docs": "https://docs.astral.sh/ruff/rules/mutable-argument-default/"
    },
    "E501": {
        "title": "Line Too Long",
        "recommendation": "Line exceeds the standard length limit. Break long expressions or docstrings across multiple lines to improve readability.",
        "docs": "https://docs.astral.sh/ruff/rules/line-too-long/"
    },
    "W291": {
        "title": "Trailing Whitespace",
        "recommendation": "Unnecessary spaces at the end of the line. Remove trailing whitespace to maintain clean git diffs.",
        "docs": "https://docs.astral.sh/ruff/rules/trailing-whitespace/"
    },
    "W293": {
        "title": "Blank Line Contains Whitespace",
        "recommendation": "Blank line contains tabs or spaces. Delete them so empty lines are truly blank.",
        "docs": "https://docs.astral.sh/ruff/rules/blank-line-contains-whitespace/"
    }
}


def get_recommendation_for_rule(rule_id: str, default_message: str = "") -> Optional[str]:
    """
    Returns a beginner-friendly recommendation for a given rule code.
    If the rule is in our curated knowledge base, returns the educational guidance.
    Otherwise, generates an informative suggestion.
    """
    rule_info = RULE_KNOWLEDGE_BASE.get(rule_id.upper())
    if rule_info:
        return rule_info["recommendation"]

    # Fallback heuristic based on rule prefix
    prefix = rule_id[0].upper() if rule_id else ""
    if prefix == "B" and len(rule_id) > 1 and rule_id[1].isdigit():
        return f"Security risk identified ({rule_id}). Review the implementation to ensure untrusted input or insecure defaults cannot be exploited."
    elif prefix == "F":
        return f"Code quality issue ({rule_id}). Ensure all referenced variables and imports are defined, and unused objects are cleaned up."
    elif prefix in ("E", "W"):
        return f"PEP 8 style convention ({rule_id}). Adjust formatting or syntax structure for consistency with Python best practices."

    return "Review the code location and apply Python best practices to resolve this warning."


def get_docs_for_rule(rule_id: str) -> Optional[str]:
    """
    Returns the documentation URL for a given rule code.
    """
    rule_info = RULE_KNOWLEDGE_BASE.get(rule_id.upper())
    if rule_info and "docs" in rule_info:
        return rule_info["docs"]
    return None
