"""Drill 03.3: a role changes style; only context adds knowledge."""
from llm import get_client, MODEL

client = get_client()

QUESTION = "What is the Retake Pass and should I buy it?"
FACTS = ("<policy>Retake Pass (fictional TrainCrest add-on): one free exam retake voucher. "
         "Costs 15% of the course price. Must be bought before the course ends. "
         "Refunded in full if the course is cancelled.</policy>")

ROLES = {
    "no role": None,
    "certification expert, no facts": "You are TrainCrest's most senior certification expert.",
    "friendly agent + facts": "You are a friendly TrainCrest support agent writing to a learner taking "
                              f"their first certification. Use simple words, under 80 words. {FACTS}",
    "trainer + facts": "You are training a new TrainCrest support agent on their first day. "
                       f"Be precise and list what the agent must check before selling it. {FACTS}",
}

for label, system in ROLES.items():
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": QUESTION}]
    r = client.chat.completions.create(model=MODEL, messages=messages)
    print(f"\n===== {label} =====\n{r.choices[0].message.content.strip()}")
