"""Run one real chat turn through a milestone's ChatService and print it like the CLI."""
import sys

from app.chat import ChatService
from app.llm import get_client

customer, message = sys.argv[1], sys.argv[2]
for event in ChatService(client=get_client().with_options(timeout=900)).stream("demo-session-1", message, customer_id=customer):
    if event["type"] == "tool":
        print(f"[tool] {event['name']}")
    elif event["type"] == "delta":
        print(event["text"], end="", flush=True)
    elif event["type"] == "replace":
        print("\n(replaced) " + event["text"])
    elif event["type"] == "error":
        print("ERROR", event["message"])
    elif event["type"] == "done":
        print(f"\nDONE {event['tools']} {event['tokens_in']}")
        for key in ("sources", "approvals"):
            if event.get(key):
                print(key.upper(), event[key])
