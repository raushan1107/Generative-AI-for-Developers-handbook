"""Lab 1, Exercise 3: a small AI-powered app: user input, streaming responses, conversation memory,
friendly error handling and basic logging (one JSON line per turn in chat_log.jsonl).
Run:  python l1_chat.py        Type 'exit' to quit, '/reset' to start a new conversation."""
import json
import time

import openai

from client import CHAT_MODEL, get_client

SYSTEM = ("You are Traincrest Assist, the friendly learner-support assistant of TrainCrest, a technical "
          "training company. Answer in at most 80 words. If you don't know a TrainCrest policy, say so.")
MAX_PAIRS = 6                          # remember the last 6 questions and answers
client = get_client()
history = []


def log(**fields):
    with open("chat_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": CHAT_MODEL, **fields}) + "\n")


def reply(question):
    """Stream one answer and return (text, stats)."""
    messages = [{"role": "system", "content": SYSTEM}] + history[-MAX_PAIRS * 2:] + [{"role": "user", "content": question}]
    start, first, parts, usage = time.perf_counter(), None, [], None
    stream = client.chat.completions.create(model=CHAT_MODEL, messages=messages, stream=True,
                                            stream_options={"include_usage": True})
    for chunk in stream:
        if chunk.usage:
            usage = chunk.usage
        if chunk.choices and chunk.choices[0].delta.content:
            first = first or time.perf_counter() - start
            parts.append(chunk.choices[0].delta.content)
            print(chunk.choices[0].delta.content, end="", flush=True)
    stats = {"first_word_s": round(first or 0, 2), "total_s": round(time.perf_counter() - start, 2),
             "tokens_in": usage.prompt_tokens if usage else None, "tokens_out": usage.completion_tokens if usage else None}
    return "".join(parts), stats


print(f"Traincrest Assist (open-source edition, {CHAT_MODEL}). Type 'exit' to quit, '/reset' for a new chat.\n")
while True:
    question = input("You: ").strip()
    if question.lower() in {"exit", "quit"}:
        break
    if question == "/reset":
        history.clear()
        print("(new conversation)\n")
        continue
    if not question:
        continue
    print("Assist: ", end="", flush=True)
    try:
        answer, stats = reply(question)
    except openai.APIConnectionError:
        print("I can't reach the model server. Is Ollama running? Start it and try again.\n")
        log(error="connection")
        continue
    except openai.NotFoundError:
        print(f"The model '{CHAT_MODEL}' isn't available. Run: ollama pull {CHAT_MODEL}\n")
        log(error="model_not_found")
        continue
    history += [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
    print(f"\n  ({stats['first_word_s']}s to first word · {stats['total_s']}s · "
          f"{stats['tokens_in']} in / {stats['tokens_out']} out)\n")
    log(question_chars=len(question), **stats)
