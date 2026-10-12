"""Drill 07.6: one request, several dependent steps. Watch the trace: each step uses what the
previous ones found (enrolment id -> course id -> dates and fee -> the move).
Run:  python lab07_06_multi_step.py"""
import desk
from agent import Agent, print_step
from desk_tools import SYSTEM, WRITE_TOOLS, kit
from llm import MODEL, get_client

REQUEST = ("I'm Diego. I can't make my AZ-104 class this week. Please move me to the next available date, "
           "tell me what it costs, and tell me when my lab will open.")

agent = Agent(get_client(), MODEL, kit, SYSTEM, max_steps=8, write_tools=WRITE_TOOLS,
              approve=lambda name, arguments, context: (True, "demo"), on_step=print_step)
print("TRACE")
result = agent.run(REQUEST, {"learner": "L-DIEGO"})
print(f"\nANSWER: {result.answer}")
print(f"stopped: {result.stopped or 'no, finished'} · model calls: {result.llm_calls} · tokens: {result.tokens}")
print("changes:", desk.ACTIONS or "none")
