import os
import json
from dotenv import load_dotenv
import anthropic
from pathlib import Path

from tools import tool_definitions, execute_tool
from prompt import build_system_prompt
from permissions import check_permission
from context import maybe_compact
from memory import recall_memories
from subagent import run_sub_agent 
from mcp_client import connect_mcp

load_dotenv()

MODEL = os.environ.get("MINI_MODEL", "Qwen3.5-4B-GGUF")  

# NOT IN THE TUTORIAL: lets the model know it is in plan mode.
PLAN_BLOCKED_TOOLS = ("write_file", "edit_file", "run_shell")

PLAN_MODE_PROMPT = """
# Plan Mode (ACTIVE)
You are in plan mode, a read-only planning phase. Your job is to produce a plan, not to make changes.
 - You may explore with read_file, list_files and grep_search.
 - write_file, edit_file and run_shell are unavailable. Never claim to have changed, created, or run anything.
 - Do not implement the task. Describe what you would do instead.
 - Write the plan as your reply, in this format:
     Goal: one sentence.
     Files to change: file_path and what changes in each.
     Steps: numbered, in order.
     Risks / open questions: anything the user should decide.
 - End by asking the user to approve. They will leave plan mode and tell you to proceed."""


class Agent:
    def __init__(self) -> None:
        # "client moves into the Agent constructor"
        self.client = anthropic.Anthropic()
        # "messages becomes this.messages on the instance"
        self.messages: list = []
        self.mode = "default" # "plan" makes the agent read-only
        self.mcp = None

    def chat(self, user_text: str) -> None:
        self.messages.append({"role": "user", "content": user_text})
        self._ensure_mcp() # discover external MCP tools before the loop

        while True:
            # Before each model call, compact the history if it has grown too long.
            self.messages = maybe_compact(self.messages, self.client, MODEL)
            system = build_system_prompt()
            # Recall memories relevant to what the user just asked, into the prompt.
            system += recall_memories(user_text)
            # Merge in any external MCP tools, prefixed so we can route their calls back. 
            mcp_tools = [{
                "name": f"mcp__demo__{t['name']}",
                "description": t["description"],
                "input_schema": t["input_schema"]
                } for t in (self.mcp.tools if self.mcp else [])]
            tools = tool_definitions + mcp_tools
            if self.mode == "plan":
                # NOT IN THE TUTORIAL: tell the model, and hide the tools it can't use.
                system += PLAN_MODE_PROMPT
                tools = [t for t in tools if t["name"] not in PLAN_BLOCKED_TOOLS]
            kwargs = dict(model=MODEL, max_tokens=4096, system=system, tools=tools, messages=self.messages)

            # Stream the reply so text shows up as it is generated, then collect 
            # the finished message (same shape a non-streaming call would return).
            with self.client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                reply = stream.get_final_message()
            print()

            # Record the assistant's full reply (text + any tool calls).
            self.messages.append({"role": "assistant", "content": reply.content})

            tool_uses = [b for b in reply.content if b.type == "tool_use"]
            # No tool calls means the model is done with this turn.
            if not tool_uses:
                return

            # Run every requested tool; send the outputs back as one user message.
            results = []
            for tu in tool_uses:
                print(f"  → {tu.name}({json.dumps(tu.input)})")
                # The 'agent' tool forks a read-only sub-agent with its own context.
                if tu.name == "agent":
                    summary = run_sub_agent(tu.input.get("task", ""), self.client, MODEL)
                    results.append({"type": "tool_result", "tool_use_id": tu.id, "content": summary})
                    continue
                # MCP tools (mcp__server__tool) go to the MCP server, not run locally.
                if tu.name.startswith("mcp__"):
                    # mcp__<server>__<tool> -> <tool>; drop the first two "__"
                    # segments so it strips the same way the TypeScript side does.
                    tool_name = "__".join(tu.name.split("__")[2:])
                    output = self.mcp.call_tool(tool_name, tu.input) if self.mcp else "Denied: no MCP server connected."
                    results.append({"type": "tool_result", "tool_use_id": tu.id, "content": output})
                    continue
                # Plan mode is read-only: writes and shell are denied on top of the gate.
                blocked = check_permission(tu.name, tu.input) == "deny" or (
                    self.mode == "plan" and tu.name in PLAN_BLOCKED_TOOLS)
                output = f"Denied: {tu.name} was blocked ({self.mode} mode)." if blocked \
                    else execute_tool(tu.name, tu.input)
                results.append({"type": "tool_result", "tool_use_id": tu.id, "content": output})
            self.messages.append({"role": "user", "content": results})

    # Connect to the MCP server named in MINI_MCP_SERVER once, on first use.
    def _ensure_mcp(self):
        mcp_env = os.environ.get("MINI_MCP_SERVER")
        if self.mcp is None and mcp_env:
            mcp_path = str(Path(mcp_env).resolve())
            self.mcp = connect_mcp("node", [mcp_path])

    def set_model(self, m: str) -> None:
        self.mode = m

    def history(self):
        return self.messages

    def load_history(self, messages) -> None:
        self.messages = messages

    def clear_history(self) -> None:
        self.messages = []