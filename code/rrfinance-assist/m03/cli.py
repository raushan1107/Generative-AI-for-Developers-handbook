"""RR Finance Assist in the terminal, milestone 3: same ChatService as the web app, streamed.

Run from the project folder:  python cli.py
"""
import uuid

from app.chat import ChatService
from app.config import MODEL, PROVIDER


def main():
    chat, session = ChatService(), uuid.uuid4().hex
    print(f"RR Finance Assist v0.3 [{PROVIDER} · {MODEL}]. Type 'exit' to quit, '/reset' for a new chat.\n")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in {"exit", "quit"}:
            break
        if question == "/reset":
            chat.reset(session)
            print("(new conversation)\n")
            continue
        if not question:
            continue
        print("Assist: ", end="", flush=True)
        for event in chat.stream(session, question):
            if event["type"] == "delta":
                print(event["text"], end="", flush=True)
            elif event["type"] == "error":
                print(event["message"])
            elif event["type"] == "done":
                print(f"\n  ({event['ttft_s']}s to first word · {event['total_s']}s · "
                      f"{event['tokens_in']} in / {event['tokens_out']} out · ${event['cost_usd']})")
        print()


if __name__ == "__main__":
    main()
