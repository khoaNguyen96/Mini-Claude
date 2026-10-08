import os

# SKILLS_DIR is used by resolve_skill() but never defined in the chapter's step code.
# The text says skills live "under .mini-skills/". 
SKILLS_DIR = ".mini-skills"


# kept from Chapter 3, the chapter's step diff does not change prompt.py so it stays an empty stub.
def build_skill_descriptions() -> str:
    return ""


def resolve_skill(text):
    if not text.startswith("/"):
        return None
    name, _, rest = text[1:].partition(" ")
    path = os.path.join(SKILLS_DIR, f"{name}.md")
    if not os.path.exists(path):
        return None
    prompt = open(path, encoding="utf-8").read().strip()
    args = rest.strip()
    return f"{prompt}\n\n{args}" if args else prompt 
