"""Drill 01.9: knowledge from training vs knowledge handed over in the prompt."""
from llm import get_client, MODEL

client = get_client()


def ask(messages):
    r = client.chat.completions.create(model=MODEL, messages=messages)
    return r.choices[0].message.content.strip()


question = "What does RR Finance Bank charge if my account is overdrawn by $80 at the end of the day?"

print("1) WITHOUT the facts:\n", ask([{"role": "user", "content": question}]))

POLICY = """RR Finance Bank overdraft policy (fictional, effective 1 October 2026)
- Overdrawn by more than $50 at the end of the day: $29 overdraft fee, at most 3 fees per day.
- Overdrawn by $50 or less at the end of the day: no fee.
- One overdraft fee per account can be refunded as a courtesy every 12 months."""

RULES = "Answer only from the policy provided. If the policy doesn't cover it, say so."

print("\n2) WITH the facts in the prompt:\n", ask([
    {"role": "system", "content": RULES},
    {"role": "user", "content": f"Policy:\n{POLICY}\n\nQuestion: {question}"},
]))

print("\n3) A question the policy doesn't cover:\n", ask([
    {"role": "system", "content": RULES},
    {"role": "user", "content": f"Policy:\n{POLICY}\n\nQuestion: What is the late fee on my credit card bill?"},
]))
