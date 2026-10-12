"""Drill 02.5: the API is stateless. You build the memory."""
from llm import get_client, MODEL

client = get_client()
SYSTEM = {"role": "system", "content": "You are Traincrest Assist, TrainCrest's learner-support assistant. One short sentence per reply."}


def chat(messages):
    r = client.chat.completions.create(model=MODEL, messages=messages)
    return r.choices[0].message.content.strip(), r.usage.prompt_tokens


# 1) Two independent calls: the second knows nothing about the first
print("1) No memory")
print("   ", chat([SYSTEM, {"role": "user", "content": "Hi, I'm Diego. I'm enrolled in the AZ-305 course."}])[0])
print("   ", chat([SYSTEM, {"role": "user", "content": "Which course am I enrolled in?"}])[0])

# 2) Same questions, but we keep and resend the history ourselves
print("\n2) Memory = resending history")
history = [SYSTEM]
for turn in ["Hi, I'm Diego. I'm enrolled in the AZ-305 course.", "Which course am I enrolled in?", "And what's my name?"]:
    history.append({"role": "user", "content": turn})
    reply, tokens_in = chat(history)
    history.append({"role": "assistant", "content": reply})
    print(f"   [{tokens_in:4} tokens in] {turn}\n                     -> {reply}")

# 3) The system message steers everything
print("\n3) Swap the system message")
grumpy = [{"role": "system", "content": "You are a grumpy pirate. One sentence."},
          {"role": "user", "content": "When does my course start?"}]
print("   ", chat(grumpy)[0])

# 4) Assistant messages you write yourself teach a pattern
print("\n4) Teach a format with example turns")
pattern = [SYSTEM,
           {"role": "user", "content": "Status of TC-10001"},
           {"role": "assistant", "content": "STATUS: CONFIRMED | STARTS: 12 Jan"},
           {"role": "user", "content": "Status of TC-10002"},
           {"role": "assistant", "content": "STATUS: WAITLISTED | STARTS: 2 Feb"},
           {"role": "user", "content": "Status of TC-10293"}]
print("   ", chat(pattern)[0])
