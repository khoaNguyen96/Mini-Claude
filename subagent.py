from tools import tool_definitions, execute_tool

# EXPLORE_TOOLS is used by run_sub_agent() but never defined in the chapter's step code.
# The sub-agent is described as read-only, so it gets the three read tools (the same ones plan mode leaves available)
EXPLORE_TOOLS = ("read_file", "list_files", "grep_search")

# the chapter's step diff does not change prompt.py in the chapter so it stays an empty sub
def build_agent_descriptions() -> str:
    return ""


def run_sub_agent(task, client, model):
    messages = [{"role": "user", "content": task}]
    tools = [ t for t in tool_definitions if t["name"] in EXPLORE_TOOLS]

    while True:
        reply = client.messages.create(
            model=model, max_tokens=4096,
            system="You are an explore sub-agent. Investigate read-only and report back a concise summary.",
            tools=tools, messages=messages
        )
        messages.append({"role":"assistant", "content": reply.content})

        tool_uses = [b for b in reply.content if b.type == "tool_use"]
        if not tool_uses:
            return "".join(b.text for b in reply.content if b.type == "text")
        results = []
        for tu in tool_uses:
            # Read-only: a sub-agent can look but not touch
            output = execute_tool(tu.name, tu.input) if tu.name in EXPLORE_TOOLS \
                else "Denied: the sub-agent is read-only"
            results.append({"type": "tool_result", "tool_use_id": tu.id, "content": output})
        messages.append({"role": "user", "content": results})



