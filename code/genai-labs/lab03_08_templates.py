"""Drill 03.8: use versioned templates, and log which version answered."""
from llm import get_client, MODEL
from prompts import render

client = get_client()
ticket = ("Customer RR-10293: charged twice for a $412 SkyHigh Airlines ticket on 9 Feb, dispute raised 4 Mar. "
          "Replacement card not received, old card expired 28 Feb. Flying abroad on 12 Mar.")

for version in ("summarise_ticket@v1", "summarise_ticket@v2"):
    prompt, used = render(version, ticket=ticket)
    r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}])
    print(f"\n[{used}] {r.usage.prompt_tokens} in / {r.usage.completion_tokens} out\n"
          f"{r.choices[0].message.content.strip()}")

prompt, used = render("reply_to_customer@v1", customer_name="Diego", language="Spanish", max_words=60,
                      message="My replacement card still hasn't arrived and I travel abroad next week.")
r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}])
print(f"\n[{used}]\n{r.choices[0].message.content.strip()}")

# A forgotten placeholder fails in code, before you pay for a confused model call.
try:
    render("reply_to_customer@v1", customer_name="Diego", message="Hi")
except KeyError as missing:
    print(f"\nCaught before calling the model: missing placeholder {missing}")
