"""Drill 01.9: knowledge from training vs knowledge handed over in the prompt."""
from llm import get_client, MODEL

client = get_client()


def ask(messages):
    r = client.chat.completions.create(model=MODEL, messages=messages)
    return r.choices[0].message.content.strip()


question = "What is TrainCrest's refund policy if I cancel 10 days before my course starts?"

print("1) WITHOUT the facts:\n", ask([{"role": "user", "content": question}]))

POLICY = """TrainCrest cancellation policy (fictional, effective 1 October 2026)
- Cancel 14 or more days before the start date: 100% refund.
- Cancel 7 to 13 days before the start date: 50% refund.
- Cancel less than 7 days before: no refund, but one free reschedule."""

RULES = "Answer only from the policy provided. If the policy doesn't cover it, say so."

print("\n2) WITH the facts in the prompt:\n", ask([
    {"role": "system", "content": RULES},
    {"role": "user", "content": f"Policy:\n{POLICY}\n\nQuestion: {question}"},
]))

print("\n3) A question the policy doesn't cover:\n", ask([
    {"role": "system", "content": RULES},
    {"role": "user", "content": f"Policy:\n{POLICY}\n\nQuestion: Can I transfer my seat to a colleague?"},
]))
