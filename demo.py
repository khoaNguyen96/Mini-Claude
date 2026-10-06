import sys

from agent import Agent

prompt = " ".join(sys.argv[1:]) or "Read greeting.txt and tell me what it says."
Agent().chat(prompt)