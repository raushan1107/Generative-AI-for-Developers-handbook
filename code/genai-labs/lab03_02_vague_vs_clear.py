"""Drill 03.2: a vague and a clear prompt, three runs each, on the same support thread."""
from llm import get_client, MODEL

client = get_client()

THREAD = """Learner (Mei, 2 Mar): Hi, I'm enrolled in Generative AI for Developers, enrolment TC-10293. The lab VM won't start, it says "quota exceeded".
Agent (3 Mar): Sorry Mei! Could you send a screenshot of the error?
Learner (3 Mar): Sent. Also my exam voucher hasn't arrived, and my course ended on 28 Feb.
Agent (4 Mar): Thanks, escalated the lab issue to the platform team.
Learner (6 Mar): No update for 2 days?? My exam is booked for 12 Mar. I need the lab and the voucher before then."""

VAGUE = f"Summarise this.\n\n{THREAD}"

CLEAR = f"""Summarise this support thread for the agent who will handle it next.
- Exactly 3 bullet points, each under 15 words.
- Bullet 1: the problems and the enrolment ID. Bullet 2: what has been done so far.
  Bullet 3: what the learner needs, and by when.
- Use only facts from the thread.

<thread>
{THREAD}
</thread>"""

for label, prompt in (("VAGUE", VAGUE), ("CLEAR", CLEAR)):
    print(f"\n===== {label} =====")
    for i in range(3):
        r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}])
        text = r.choices[0].message.content.strip()
        print(f"\n--- run {i + 1} · {len(text.split())} words ---\n{text}")
