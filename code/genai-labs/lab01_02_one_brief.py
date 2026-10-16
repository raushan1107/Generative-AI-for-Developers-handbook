"""Drill 01.2: one model, one brief, three very different kinds of output."""
from llm import get_client, MODEL

client = get_client()

BRIEF = ("RR Finance Bank is launching High-Yield Savings on 1 March 2027: a savings account "
         "paying 4.10% APY, with no monthly fee and no minimum balance, opened in the mobile app.")

TASKS = {
    "Marketing text": "Write a 40-word announcement for the bank's app home screen.",
    "Python code": "Write a Python function monthly_interest(balance: float) -> float for this account. Code only.",
    "JSON record": 'Return only JSON with keys "product", "launch_date" (YYYY-MM-DD), "apy_pct", "monthly_fee_usd".',
}

for label, task in TASKS.items():
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": f"{BRIEF}\n\n{task}"}],
    )
    print(f"\n===== {label} =====")
    print(response.choices[0].message.content.strip())
