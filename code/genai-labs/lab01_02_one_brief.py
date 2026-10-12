"""Drill 01.2: one model, one brief, three very different kinds of output."""
from llm import get_client, MODEL

client = get_client()

BRIEF = ("TrainCrest is launching a 3-day online course, 'Generative AI for Developers', "
         "starting on 20 March 2027, priced at $1,200, with hands-on labs on Azure.")

TASKS = {
    "Marketing text": "Write a 40-word announcement for LinkedIn.",
    "Python code": "Write a Python function days_until_start(today: date) -> int for this course. Code only.",
    "JSON record": 'Return only JSON with keys "title", "start_date" (YYYY-MM-DD), "price_usd", "format".',
}

for label, task in TASKS.items():
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": f"{BRIEF}\n\n{task}"}],
    )
    print(f"\n===== {label} =====")
    print(response.choices[0].message.content.strip())
