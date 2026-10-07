import re
from pathlib import Path

_DANGEROUS = [
    r"\brm\s+-rf\b",
    r"\bgit\s+push\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bsudo\b",
    r"\bmkfs\b",
    r">\s*/dev/",
]

def check_permission(name: str, inp: dict) -> str:
    if name == "run_shell" and any(re.search(p, str(inp.get("command", ""))) for p in _DANGEROUS):
        return "deny"
    if name in ["write_file", "edit_file"]:
        file_path = inp.get("file_path", "")
        if not _check_path_inside_cwd(file_path):
            return "deny"
    return "allow"

def _check_path_inside_cwd(file_path: str) -> bool:
    try:
        cwd = Path.cwd().resolve()
        target = (cwd / file_path).resolve()
        # Returns True only if 'target' is inside or equal to 'cwd'
        return cwd in target.parents or target == cwd
    except Exception:
        return False


