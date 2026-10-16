"""Drill 07.1: chatbot vs agent. The same request to a model with no tools, then to an agent
with tools over RR Finance Bank's (stand-in) systems. Then look at what actually changed."""
import desk
from agent import Agent, print_step
from desk_tools import SYSTEM, WRITE_TOOLS, kit
from llm import MODEL, get_client

REQUEST = "Hi, it's Mei. I think I left my Cashback Card in a taxi. Please freeze it and tell me what that means."
client = get_client()

print("CHATBOT (no tools)")
reply = client.chat.completions.create(model=MODEL, messages=[
    {"role": "system", "content": SYSTEM}, {"role": "user", "content": REQUEST}]).choices[0].message.content
print(" ", reply.strip())
print("  changes in RR Finance Bank's systems:", desk.ACTIONS or "none")

print("\nAGENT (tools; approvals granted automatically for this demo, see Drill 07.7)")
agent = Agent(client, MODEL, kit, SYSTEM, write_tools=WRITE_TOOLS,
              approve=lambda name, arguments, context: (True, "demo"), on_step=print_step)
result = agent.run(REQUEST, {"customer": "RR-10293"})
print(" ", result.answer)
print("  changes in RR Finance Bank's systems:", desk.ACTIONS or "none")
print(f"  model calls: {result.llm_calls}, tool steps: {len(result.steps)}")
