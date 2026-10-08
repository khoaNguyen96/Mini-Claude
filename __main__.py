# Entry point: parse argv, then run one-shot or REPL.
import sys

from agent import Agent
from session import save_session, load_session
from skills import resolve_skill

def main(argv=None) -> None: 
    # PLACEHOLDER: the chapter shows only the changed lines of this function.
    # Everything except the marked additions below is inferred from the diff's 
    # context lines (agent = Agent(), one-shot, text = one_shot, the exit check).
    # A tiny REPL: read a line, hand it to the agent, repeat. One-shot mode runs a
    # single prompt from the command line and exits. 
    if argv is None: 
        argv = sys.argv[1:]

    agent = Agent()
    # --resume: reload the saved conversataion before doing anything else.
    resume = "--resume" in argv
    if resume:
        saved = load_session()
        if saved:
            agent.load_history(saved)
            print(f"(resumed {len(saved)} messages)")

    one_shot = " ".join(argv).strip()
    if one_shot:
        # "/name ..." runs a skill's prompt templatel anything else is a message
        text = resolve_skill(one_shot) or one_shot
        agent.chat(text)
        save_session(agent.history())
        return

    print("mini-claude (type 'exit' to quit)")
    while True:
        try: # PLACEHOLDER
            line = input("> ").strip() # PLACEHOLDER
        except (EOFError, KeyboardInterrupt):
            break # PLACEHOLDER
        if line in ("exit", "quit"):
            break
        if line == "/clear":
            agent.clear_history()
            save_session(agent.history())
            print("(history cleared)")
            continue
        if line:
            agent.chat(resolve_skill(line) or line)
        if line:
            save_session(agent.history())

# PLACEHOLDER: cut off in the chapter's diff; inferred so the file can be run
if __name__ == "__main__":
    main()