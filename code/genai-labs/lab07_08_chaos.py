"""Drill 07.8: run the same task while services fail 30% of the time. Count what the agent
finished, how many steps it took, and, most important, whether the systems ended up in a
correct state: one dispute at most, never two (two would mean a double credit)."""
import desk
from agent import Agent
from desk_tools import SYSTEM, WRITE_TOOLS, kit
from llm import MODEL, get_client

client = get_client()
TASK = "Please dispute the duplicate SkyHigh Airlines charge on my Cashback Card and tell me when I'll get the money."
print(f"{'seed':>4} {'finished':>9} {'steps':>6} {'errors':>7} {'disputes':>9}  answer")
for seed in range(1, 6):
    desk.reset(flaky_rate=0.3, seed=seed)
    agent = Agent(client, MODEL, kit, SYSTEM, max_steps=8, write_tools=WRITE_TOOLS,
                  approve=lambda *a: (True, "demo"))
    result = agent.run(TASK, {"customer": "RR-10293"})
    errors = sum(s.status == "error" for s in result.steps)
    disputes = sum(a["action"] == "open_dispute" for a in desk.ACTIONS)
    print(f"{seed:>4} {('yes' if not result.stopped else result.stopped):>9} {len(result.steps):>6} {errors:>7} "
          f"{disputes:>9}  {result.answer[:70]}")
