import os
import json
from dotenv import load_dotenv
import anthropic

from tools import tool_definitions, execute_tool
from prompt import build_system_prompt

load_dotenv()

MODEL = os.environ.get("MINI_MODEL", "Qwen3.5-4B-GGUF")  


class Agent:
    def __init__(self) -> None:
        # "client moves into the Agent constructor"
        self.client = anthropic.Anthropic()
        # "messages becomes this.messages on the instance"
        self.messages: list = []

    def chat(self, user_text: str) -> None:
        self.messages.append({"role": "user", "content": user_text})

        while True:
            system = build_system_prompt()
            tools = tool_definitions
            kwargs = dict(model=MODEL, max_tokens=4096, system=system, tools=tools, messages=self.messages)

            reply = self.client.messages.create(**kwargs)
            for block in reply.content:
                if block.type == "text":
                    print(block.text, end="", flush=True)
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
                output = execute_tool(tu.name, tu.input)
                results.append({"type": "tool_result", "tool_use_id": tu.id, "content": output})
            self.messages.append({"role": "user", "content": results})

    def history(self):
        return self.messages

    def load_history(self, messages) -> None:
        self.messages = messages

    def clear_history(self) -> None:
        self.messages = []