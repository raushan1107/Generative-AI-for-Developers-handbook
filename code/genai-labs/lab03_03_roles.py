"""Drill 03.3: a role changes style; only context adds knowledge."""
from llm import get_client, MODEL

client = get_client()

QUESTION = "What is the Balance Transfer Card and should I get it?"
FACTS = ("<policy>Balance Transfer Card (fictional RR Finance Bank product): 0% APR for 18 months on balances "
         "transferred in the first 60 days, then 21.99% APR. A 3% fee on each transfer. No annual fee. "
         "Approval depends on a credit check. Staff explain products; they don't tell customers what to buy.</policy>")

ROLES = {
    "no role": None,
    "credit card expert, no facts": "You are RR Finance Bank's most senior credit card expert.",
    "friendly agent + facts": "You are a friendly RR Finance Bank support agent writing to a customer who has "
                              f"never had a credit card. Use simple words, under 80 words. {FACTS}",
    "trainer + facts": "You are training a new RR Finance Bank support agent on their first day. "
                       f"Be precise and list what the agent must check before discussing it with a customer. {FACTS}",
}

for label, system in ROLES.items():
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": QUESTION}]
    r = client.chat.completions.create(model=MODEL, messages=messages)
    print(f"\n===== {label} =====\n{r.choices[0].message.content.strip()}")
