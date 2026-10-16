"""Drill 03.2: a vague and a clear prompt, three runs each, on the same bank support thread."""
from llm import get_client, MODEL

client = get_client()

THREAD = """Customer (Mei, 2 Mar): Hi, customer RR-10293. I was charged twice for a $412 SkyHigh Airlines ticket on my Cashback Card.
Agent (3 Mar): Sorry Mei! Could you confirm the dates of both payments?
Customer (3 Mar): Both on 9 Feb. Also my replacement card hasn't arrived, and the old one expired on 28 Feb.
Agent (4 Mar): Thanks, I've raised a dispute for the duplicate payment.
Customer (6 Mar): No update for 2 days?? I fly abroad on 12 Mar. I need the new card and the $412 back before then."""

VAGUE = f"Summarise this.\n\n{THREAD}"

CLEAR = f"""Summarise this support thread for the agent who will handle it next.
- Exactly 3 bullet points, each under 15 words.
- Bullet 1: the problems and the customer ID. Bullet 2: what has been done so far.
  Bullet 3: what the customer needs, and by when.
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
