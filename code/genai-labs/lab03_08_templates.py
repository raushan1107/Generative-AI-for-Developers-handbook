"""Drill 03.8: use versioned templates, and log which version answered."""
from llm import get_client, MODEL
from prompts import render

client = get_client()
ticket = ("Enrolment TC-10293: lab VM shows 'quota exceeded'. Exam voucher not received, course ended 28 Feb. "
          "Exam booked for 12 Mar.")

for version in ("summarise_ticket@v1", "summarise_ticket@v2"):
    prompt, used = render(version, ticket=ticket)
    r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}])
    print(f"\n[{used}] {r.usage.prompt_tokens} in / {r.usage.completion_tokens} out\n"
          f"{r.choices[0].message.content.strip()}")

prompt, used = render("reply_to_learner@v1", learner_name="Diego", language="Spanish", max_words=60,
                      message="My voucher still hasn't arrived and my exam is next week.")
r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}])
print(f"\n[{used}]\n{r.choices[0].message.content.strip()}")

# A forgotten placeholder fails in code, before you pay for a confused model call.
try:
    render("reply_to_learner@v1", learner_name="Diego", message="Hi")
except KeyError as missing:
    print(f"\nCaught before calling the model: missing placeholder {missing}")
