"""Drill 02.14: a cost meter. Usage -> dollars -> monthly projection. Also logs to usage.jsonl."""
import json
import os
import time

from llm import get_client, MODEL

PRICE_IN = float(os.getenv("PRICE_IN_PER_M", "0.40"))     # USD per 1M input tokens
PRICE_OUT = float(os.getenv("PRICE_OUT_PER_M", "1.60"))   # USD per 1M output tokens
TURNS_PER_MONTH = 25_000 * 4                              # TrainCrest: conversations x average turns

client = get_client()


def cost_usd(usage):
    return (usage.prompt_tokens * PRICE_IN + usage.completion_tokens * PRICE_OUT) / 1_000_000


LEAN = "You are Traincrest Assist, TrainCrest's learner-support assistant. Be brief and friendly."
BLOATED = LEAN + " Always follow the TrainCrest tone guide and be warm and professional." * 120
question = "My lab environment expired before I finished the final exercise. What can I do?"

for label, system in [
    ("bloated prompt", BLOATED),
    ("lean prompt", LEAN),
    ("lean + 'under 60 words'", LEAN + " Answer in under 60 words."),
]:
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": question}])
    u = r.usage
    details = getattr(u, "completion_tokens_details", None)
    reasoning = getattr(details, "reasoning_tokens", 0) or 0
    per_turn = cost_usd(u)
    print(f"{label:26} {u.prompt_tokens:5} in · {u.completion_tokens:4} out ({reasoning} reasoning) · "
          f"${per_turn:.5f}/turn · ~${per_turn * TURNS_PER_MONTH:,.0f}/month")
    with open("usage.jsonl", "a", encoding="utf-8") as log:
        log.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "label": label, "model": MODEL,
                              "tokens_in": u.prompt_tokens, "tokens_out": u.completion_tokens,
                              "cost_usd": round(per_turn, 6)}) + "\n")
