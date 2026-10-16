"""Drill 02.7: generation parameters, and which ones your model accepts."""
import openai

from llm import get_client, MODEL

client = get_client()


def try_call(label, prompt, **params):
    try:
        r = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}], **params)
        c = r.choices[0]
        text = (c.message.content or "").strip().replace("\n", " ")
        print(f"  {label:26} -> {text[:70]!r}  [finish={c.finish_reason}, out={r.usage.completion_tokens}]")
    except openai.BadRequestError as e:
        print(f"  {label:26} -> REJECTED: {e.message[:90]}")


print("Temperature (3 samples each):")
for t in (0.0, 1.0, 1.8):
    for _ in range(3):
        try_call(f"temperature={t}", "Suggest a name for a new savings account. Name only.", temperature=t)

print("\nOutput cap:")
try_call("max_completion_tokens=40", "Explain what an overdraft is in three paragraphs.", max_completion_tokens=40)

print("\nStop sequence:")
try_call("stop=['4.']", "List 5 types of bank account, numbered 1. to 5., one per line.", stop=["4."])

print("\nReasoning effort (reasoning models only):")
for effort in ("low", "high"):
    try_call(f"reasoning_effort={effort}",
             "A customer paid three $29 overdraft fees and a $15 express card fee. The bank refunds "
             "one overdraft fee as a courtesy and the express fee in full. Total refund in USD? Number only.",
             reasoning_effort=effort)
