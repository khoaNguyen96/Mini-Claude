import os
import platform
import re
import subprocess
from pathlib import Path

# PLACEHOLDER modules: the chapter calls these from build_dynamic_system_context()
# but never shows them. They are stubs until Chapters 8 and 9 (memory, skills,
# sub-agents). Module names are inferred from the TypeScript imports.
from memory import build_memory_prompt_section
from skills import build_skill_descriptions
from subagent import build_agent_descriptions

STATIC_CORE = """You are Mini Claude Code, a small coding assistant CLI.
You help with software engineering tasks using the tools available to you.

# Doing tasks
 - Do not propose changes to code you haven't read. Read files first.
 - Do not create files unless necessary. Prefer editing existing files.
 - Avoid over-engineering. Only make changes that were requested.

# Executing actions with care
 - Prefer reversible actions. For risky or destructive ones (rm -rf, git push,
   dropping tables), confirm with the user before proceeding.

# Using your tools
 - Use read_file / edit_file / list_files / grep_search instead of shell cat,
   sed, ls, grep. Reserve run_shell for actual shell operations.
 - If several tool calls are independent, make them in parallel.

# Tone and style
 - Keep responses short and concise. Lead with the answer.
 - Reference code as file_path:line_number."""

# PLACEHOLDER: the chapter defines the text as STATIC_CORE but
# build_static_system_prompt() returns SYSTEM_PROMPT_TEMPLATE. Both names are
# aliased so each reference resolves.
SYSTEM_PROMPT_TEMPLATE = STATIC_CORE 

def load_claude_md() -> str:
    parts: list[str] = []
    d = Path.cwd().resolve()
    while True: 
        f = d / "CLAUDE.md"
        if f.is_file():
            try:
                content = f.read_text()
                content = resolve_includes(content, str(d)) # @include resolution 
                parts.insert(0, content)
            except Exception:
                pass
        parent = d.parent
        if parent == d:
            break
        d = parent
    rules = load_rules_dir(str(Path.cwd())) # .claude/rules/*.md
    claude_md = "\n\n# Project Instructions (CLAUDE.md)\n" + "\n\n---\n\n".join(parts) if parts else ""
    return claude_md + rules

def get_git_context() -> str:
    try:
        opts = {"encoding": "utf-8", "timeout": 3, "capture_output": True}
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], **opts).stdout.strip()
        log = subprocess.run(["git", "log", "--online", "-5"], **opts).stdout.strip()
        status = subprocess.run(["git", "status", "--shorts"], **opts).stdout.strip()
        result = f"\nGit branch: {branch}"
        if log:
            result += f"\nRecent Commits:\n{log}"
        if status: 
            result += f"\nGit status:\n{status}"
        return result
    except Exception:
        return ""

def build_static_system_prompt() -> str:
    # Static core: retunr the template as-is -- this is the block cached via cache_control
    return SYSTEM_PROMPT_TEMPLATE

def build_dynamic_system_context() -> str:
    # Dynamic block: environment + git + memory + skills + agent list
    plat = f"{platform.system()} {platform.machine()}"
    shell = os.environ.get("SHELL", "/bin/sh")
    return (
        f"# Environment\n"
        f"Working directory: {Path.cwd()}\n"
        f"Platform: {plat}\n"
        f"Shell: {shell}"
        f"{get_git_context()}{build_memory_prompt_section()}"
        f"{build_skill_descriptions()}{build_agent_descriptions()}"
    )

def build_user_context_reminder() -> str:
    # CLAUDE.md + date: wrapped in <system-reminder>, injected into the first user message by the agent
    from datetime import date
    return (
        "<system-reminder>\n..."
        f"{load_claude_md()}\n"
        f"# currentDate\nToday's date is {date.today().isoformat()}.\n"
        "...</system-reminder>"
    )

# PLACEHOLDER: agent.py calls build_system_prompt(), but the chapter never shows
# it. Chapter 7 (prefix caching) splits the static and dynamic blocks in the API
# call, so for now they are simply joined into one string.
def build_system_prompt() -> str:
    return build_static_system_prompt() + "\n\n" + build_dynamic_system_context()


# ---- @include resolution ----
# The chapter shows only the TypeScript for these two. This is a direct
# translation of it.

INCLUDE_REGEX = re.compile(r"^@(\./[^\s]+|~/[^\s]+|/[^\s]+)$", re.MULTILINE)
MAX_INCLUDE_DEPTH = 5


def resolve_includes(content: str, base_path: str, visited: set | None = None, depth: int = 0) -> str:
    if visited is None: 
        visited = set()
    if depth >= MAX_INCLUDE_DEPTH:
        return content

    def _replace(m: re.Match) -> str:
        raw_path = m.group(1)
        if raw_path.startswith("~/"):
            resolved = Path.home() / raw_path[2:]
        elif raw_path.startswith("/"):
            resolved = Path(raw_path)
        else:
            resolved = Path(base_path) / raw_path # ./relative
        resolved = resolved.resolve()
        key = str(resolved)
        if key in visited:
            return f"<!-- circular: {raw_path} -->"
        if not resolved.exists():
            return f"<!-- not found: {raw_path} -->"
        try:
            visited.add(key)
            included = resolved.read_text()
            return resolve_includes(included, str(resolved.parent), visited, depth + 1)
        except Exception:
            return f"<!-- error reading: {raw_path} -->"
    return INCLUDE_REGEX.sub(_replace, content)

# ---- Rules directory loading ----

def load_rules_dir(dir: str) -> str:
    rules_dir = Path(dir) / ".claude" / "rules"
    if not rules_dir.exists():
        return ""
    files = sorted(f.name for f in rules_dir.iterdir() if f.name.endswith(".md"))
    parts: list[str] = []
    for file in files:
        content = (rules_dir / file).read_text()
        content = resolve_includes(content, str(rules_dir)) # Rule files also support @include
        parts.append(f"<!-- rule: {file} -->\n{content}")
    return "\n\n## Rules\n" + "\n\n".join(parts) if parts else ""
