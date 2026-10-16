"""Drill 02.5: the API is stateless. You build the memory."""
from llm import get_client, MODEL

client = get_client()
SYSTEM = {"role": "system", "content": "You are RR Finance Assist, RR Finance Bank's customer-support assistant. One short sentence per reply."}


def chat(messages):
    r = client.chat.completions.create(model=MODEL, messages=messages)
    return r.choices[0].message.content.strip(), r.usage.prompt_tokens


# 1) Two independent calls: the second knows nothing about the first
print("1) No memory")
print("   ", chat([SYSTEM, {"role": "user", "content": "Hi, I'm Diego. I'm travelling to Japan next week."}])[0])
print("   ", chat([SYSTEM, {"role": "user", "content": "Where am I travelling?"}])[0])

# 2) Same questions, but we keep and resend the history ourselves
print("\n2) Memory = resending history")
history = [SYSTEM]
for turn in ["Hi, I'm Diego. I'm travelling to Japan next week.", "Where am I travelling?", "And what's my name?"]:
    history.append({"role": "user", "content": turn})
    reply, tokens_in = chat(history)
    history.append({"role": "assistant", "content": reply})
    print(f"   [{tokens_in:4} tokens in] {turn}\n                     -> {reply}")

# 3) The system message steers everything
print("\n3) Swap the system message")
grumpy = [{"role": "system", "content": "You are a grumpy pirate. One sentence."},
          {"role": "user", "content": "When will my replacement card arrive?"}]
print("   ", chat(grumpy)[0])

# 4) Assistant messages you write yourself teach a pattern
print("\n4) Teach a format with example turns")
pattern = [SYSTEM,
           {"role": "user", "content": "Status of payment PAY-10001"},
           {"role": "assistant", "content": "STATUS: SETTLED | DATE: 12 Jan"},
           {"role": "user", "content": "Status of payment PAY-10002"},
           {"role": "assistant", "content": "STATUS: PENDING | DATE: 2 Feb"},
           {"role": "user", "content": "Status of payment PAY-10293"}]
print("   ", chat(pattern)[0])
