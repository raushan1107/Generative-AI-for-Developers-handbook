"""RR Finance Assist in the terminal, milestone 7: same ChatService as the web app, streamed.

Run from the project folder:  python cli.py               (not signed in)
                              python cli.py --as RR-10293    (demo sign-in as Mei; also RR-20877, RR-31002)
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
        tools.set_search_service(SearchService(chat.client))     # products (milestone 5) and help centre (6)
    except Exception as e:
        print(f"(search index not available, using keyword search: {e})")
    customer = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else None
    print(f"RR Finance Assist v0.7 [{PROVIDER} · {MODEL}] signed in as {customer or 'nobody'}. "
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
        for event in chat.stream(session, question, customer_id=customer):
            if event["type"] == "tool":
                print(f"[{event['label']}...] ", end="", flush=True)
            elif event["type"] == "delta":
                print(event["text"], end="", flush=True)
            elif event["type"] == "replace":
                print("\n(replaced) " + event["text"], end="", flush=True)
            elif event["type"] == "error":
                print(event["message"])
            elif event["type"] == "done":
                for source in event.get("sources", []):          # milestone 6: what the answer cites
                    print(f"\n  [{source['n']}] {source['title']}  {source['url']}", end="")
                print(f"\n  ({event['ttft_s']}s to first word · {event['total_s']}s · "
                      f"{event['tokens_in']} in / {event['tokens_out']} out · ${event['cost_usd']})")
                for a in event.get("approvals", []):              # milestone 7: the customer decides
                    answer = input(f"  APPROVE? {a['summary']} [y/n] ").strip().lower()
                    result = chat.decide(session, a["action_id"], customer, answer == "y")
                    print(f"  {result['message']}")
        print()


if __name__ == "__main__":
    main()
