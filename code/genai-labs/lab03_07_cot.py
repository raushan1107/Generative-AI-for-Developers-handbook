"""Drill 03.7: direct answer vs step-by-step reasoning on a multi-step policy case."""
import re

from llm import get_client, MODEL

client = get_client()

POLICY = """<policy>
- Cancel 14 or more days before the start date: 100% refund of the course fee.
- Cancel 7 to 13 days before the start date: 50% refund of the course fee.
- Cancel less than 7 days before: no refund, one free reschedule instead.
- Retake Pass add-on: refunded in full whenever the course is cancelled.
</policy>"""

CASE = """<case>
Enrolment TC-10577: 'Generative AI for Developers' starting on 20 March, course fee $1,200,
plus a Retake Pass bought for $180. On 9 March the learner cancels and asks for a full
refund of $1,380.
</case>"""

DIRECT = f"{POLICY}\n{CASE}\nHow much should we refund? Answer in one sentence."
STEPWISE = f"""{POLICY}
{CASE}
Work through this inside <reasoning> tags: count the days between the cancellation and the start,
find the matching rule for the course fee, then handle the add-on. Then give the customer-facing
answer in one sentence inside <answer> tags."""

for label, prompt in (("DIRECT", DIRECT), ("STEP BY STEP", STEPWISE)):
    r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}])
    text = r.choices[0].message.content.strip()
    print(f"\n===== {label} · {r.usage.completion_tokens} output tokens =====\n{text}")

# In an app, the learner sees only the <answer> part.
match = re.search(r"<answer>(.*?)</answer>", text, re.S)
print("\nShown to the learner:", match.group(1).strip() if match else "(no <answer> tag: handle this case!)")
