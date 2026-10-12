"""Traincrest Assist in the terminal, milestone 5: same ChatService as the web app, streamed.

Run from the project folder:  python cli.py               (not signed in)
                              python cli.py --as L-MEI    (demo sign-in as Mei; also L-DIEGO, L-ASHA)
"""
import sys
import uuid

from app import tools
from app.chat import ChatService
from app.config import MODEL, PROVIDER
from app.search import SearchService


def main():
    chat, session = ChatService(), uuid.uuid4().hex
    try:
        tools.set_search_service(SearchService(chat.client))     # milestone 5: semantic course search
    except Exception as e:
        print(f"(search index not available, using keyword search: {e})")
    learner = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else None
    print(f"Traincrest Assist v0.5 [{PROVIDER} · {MODEL}] signed in as {learner or 'nobody'}. "
          "Type 'exit' to quit, '/reset' for a new chat.\n")
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
        for event in chat.stream(session, question, learner_id=learner):
            if event["type"] == "tool":
                print(f"[{event['label']}...] ", end="", flush=True)
            elif event["type"] == "delta":
                print(event["text"], end="", flush=True)
            elif event["type"] == "replace":
                print("\n(replaced) " + event["text"], end="", flush=True)
            elif event["type"] == "error":
                print(event["message"])
            elif event["type"] == "done":
                print(f"\n  ({event['ttft_s']}s to first word · {event['total_s']}s · "
                      f"{event['tokens_in']} in / {event['tokens_out']} out · ${event['cost_usd']})")
        print()


if __name__ == "__main__":
    main()
