"""Drill 03.7: direct answer vs step-by-step reasoning on a multi-step overdraft-fee case."""
import re

from llm import get_client, MODEL

client = get_client()

POLICY = """<policy>
- Account overdrawn by more than $50 at the end of the day: $29 fee per overdrawn payment, at most 3 fees per day.
- Account overdrawn by $50 or less at the end of the day: no fee.
- Fees charged against these rules are bank errors and are always refunded.
- Courtesy refund: one more overdraft fee per account every 12 months, on request.
</policy>"""

CASE = """<case>
Customer RR-10577 (Everyday Checking) was charged five $29 overdraft fees: four on 9 March, when
the account ended the day $212 overdrawn, and one on 10 March, when it ended the day $31 overdrawn.
They have not used a courtesy refund this year and ask for all $145 back.
</case>"""

DIRECT = f"{POLICY}\n{CASE}\nHow much should we refund? Answer in one sentence."
STEPWISE = f"""{POLICY}
{CASE}
Work through this inside <reasoning> tags: check each day against the fee rules, find any fees
charged in error, then apply the courtesy rule. Then give the customer-facing answer in one
sentence inside <answer> tags."""

for label, prompt in (("DIRECT", DIRECT), ("STEP BY STEP", STEPWISE)):
    r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}])
    text = r.choices[0].message.content.strip()
    print(f"\n===== {label} · {r.usage.completion_tokens} output tokens =====\n{text}")

# In an app, the customer sees only the <answer> part.
match = re.search(r"<answer>(.*?)</answer>", text, re.S)
print("\nShown to the customer:", match.group(1).strip() if match else "(no <answer> tag: handle this case!)")
