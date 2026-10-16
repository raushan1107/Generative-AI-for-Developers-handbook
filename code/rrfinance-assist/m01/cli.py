"""RR Finance Assist, milestone 1: a question goes in, an answer comes out.

Run from the project folder:  python cli.py
"""
import time

from app.config import MODEL, PROVIDER
from app.llm import get_client

SYSTEM_PROMPT = (
    "You are RR Finance Assist, the customer-support assistant of RR Finance Bank, a retail bank. "
    "Be friendly, concise and practical. Never ask for a PIN, a password or a full card number. "
    "If you don't know something about RR Finance Bank's policies or a customer's account, say so honestly."
)


def main():
    client = get_client()
    print(f"RR Finance Assist v0.1 [{PROVIDER} · {MODEL}]. Ask a question, or type 'exit'.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        start = time.perf_counter()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
        )
        seconds = time.perf_counter() - start

        print(f"\nAssist: {response.choices[0].message.content.strip()}")
        u = response.usage
        print(f"  ({seconds:.1f}s · {u.prompt_tokens} in / {u.completion_tokens} out)\n")


if __name__ == "__main__":
    main()
