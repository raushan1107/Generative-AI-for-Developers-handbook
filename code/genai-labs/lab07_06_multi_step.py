"""Drill 07.6: one request, several dependent steps. Watch the trace: each step uses what the
previous ones found (card -> transaction ID -> dispute check -> the dispute).
Run:  python lab07_06_multi_step.py"""
import desk
from agent import Agent, print_step
from desk_tools import SYSTEM, WRITE_TOOLS, kit
from llm import MODEL, get_client

REQUEST = ("I'm Mei. I was charged twice for my SkyHigh Airlines flight on my Cashback Card. Please dispute "
           "the duplicate charge and tell me when I'll get a provisional credit.")

agent = Agent(get_client(), MODEL, kit, SYSTEM, max_steps=8, write_tools=WRITE_TOOLS,
              approve=lambda name, arguments, context: (True, "demo"), on_step=print_step)
print("TRACE")
result = agent.run(REQUEST, {"customer": "RR-10293"})
print(f"\nANSWER: {result.answer}")
print(f"stopped: {result.stopped or 'no, finished'} · model calls: {result.llm_calls} · tokens: {result.tokens}")
print("changes:", desk.ACTIONS or "none")
