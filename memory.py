import os
import re

# MEMORY_DIR is used by recall_memories() but never defined in the chapter's step code.
# (The deep-dive describes a per-project hashed folder under ~/.mini-claude/projects/; the step itself just needs one directory)
MEMORY_DIR = os.path.join(os.path.expanduser("~"), ".mini-claude", "memory")

# kept from Chapter 3, the chapter's step diff does not change prompt.py, so it statys an empty stub.
def build_memory_prompt_section() -> str:
    return ""

def recall_memories(query: str) -> str:
    if not os.path.isdir(MEMORY_DIR):
        return ""
    query_words = {w for w in re.split(r"\W+", query.lower()) if len(w) > 2}

    scored = []
    for name in os.listdir(MEMORY_DIR):
        if not name.endswith(".md"):
            continue
        text = open(os.path.join(MEMORY_DIR, name), encoding="utf-8").read().strip()
        words = set(re.split(r"\W+", text.lower()))
        score = sum(1 for w in query_words if w in words)
        if score > 0:
            scored.append((score, text))
    if not scored:
        return ""

    top = "\n".join(f"- {t}" for _, t in sorted(scored, key=lambda s: -s[0])[:3])
    return f"\n\n# Memory (things you remember about the user and project)\n{top}"