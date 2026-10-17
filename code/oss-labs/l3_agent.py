"""Lab 3, Exercise 2: an agent that understands a request, selects and calls tools, processes the
results and returns a final answer. Changes need the customer's approval (you type y or n).
Run:  python l3_agent.py "I think I left my Cashback Card in a taxi. Please freeze it." """
import json
import sys

from client import AGENT_MODEL, get_client

CUSTOMER = "Mei"                                      # the signed-in customer: set by the app, not the model
CARDS = {"4821": {"product": "Cashback Card", "status": "active"},
         "1177": {"product": "Everyday Checking debit card", "status": "active"}}
AUDIT_LOG = []                                        # every real change, in order


# ---------------- tools: two reads, one write
def my_cards():
    return [{"card_last4": k, "product": v["product"]} for k, v in CARDS.items()]


def card_status(card_last4):
    c = CARDS.get(card_last4)
    if c is None:
        return {"error": f"{card_last4} is not one of {CUSTOMER}'s cards; call my_cards yourself"}
    return {"card_last4": card_last4, **c}


def freeze_card(card_last4):
    c = CARDS.get(card_last4)
    if c is None or c["status"] == "frozen":
        return {"error": "this card can't be frozen (unknown or already frozen); tell the customer"}
    c["status"] = "frozen"
    AUDIT_LOG.append({"action": "freeze_card", "card_last4": card_last4})
    return {"card_last4": card_last4, "status": "frozen", "note": "payments declined until unfrozen; direct debits keep working"}


FUNCTIONS = {"my_cards": my_cards, "card_status": card_status, "freeze_card": freeze_card}
NEEDS_APPROVAL = {"freeze_card"}


def tool(name, description, properties=None):
    params = {"type": "object", "properties": properties or {}, "required": list(properties or {})}
    return {"type": "function", "function": {"name": name, "description": description, "parameters": params}}


CARD = {"card_last4": {"type": "string", "description": "Last four digits, like 4821, from my_cards"}}
TOOLS = [tool("my_cards", "List the signed-in customer's cards with their last four digits."),
         tool("card_status", "Status of one card: active or frozen.", CARD),
         tool("freeze_card", "Freeze one card so new payments are declined. Changes the account; the customer must approve.", CARD)]
SYSTEM = (f"You are RR Finance Assist acting for the signed-in customer, {CUSTOMER}. "
          "Use tools for every fact and action; never guess card numbers. Never ask for a full card number or a PIN. "
          "The customer can't call tools; call them yourself, starting with my_cards. If an action is declined, "
          "don't retry it. Finish with a short answer saying what was done.")


def approve(name, args):
    """A person decides. The preview comes from the real data, not from the model."""
    status = card_status(args.get("card_last4", ""))
    print(f"\n  APPROVAL NEEDED: freeze the {status.get('product', '?')} ending {args.get('card_last4')} "
          f"(currently {status.get('status', 'unknown')})")
    return input("  Approve? [y/n] ").strip().lower() == "y"


def run(request, max_steps=8):
    client = get_client()
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": request}]
    for step in range(1, max_steps + 1):                      # 1 understand the task
        msg = client.chat.completions.create(model=AGENT_MODEL, messages=messages, tools=TOOLS).choices[0].message
        if not msg.tool_calls:                                # 5 final response
            return msg.content.strip()
        messages.append(msg)
        for call in msg.tool_calls:                           # 2 select a tool
            name, args = call.function.name, json.loads(call.function.arguments or "{}")
            if name in NEEDS_APPROVAL and not approve(name, args):
                result = {"error": "the customer declined this action"}
            elif name in FUNCTIONS:
                try:
                    result = FUNCTIONS[name](**args)          # 3 execute the tool
                except TypeError as e:
                    result = {"error": f"bad arguments: {e}"}
            else:
                result = {"error": f"unknown tool {name}"}
            print(f"  step {step}: {name}({args}) -> {json.dumps(result)}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
            # 4 the result goes back to the model, which evaluates it and decides the next step
    return "Sorry, that needed more steps than I'm allowed."


if __name__ == "__main__":
    request = sys.argv[1] if len(sys.argv) > 1 else "I think I left my Cashback Card in a taxi. Please freeze it."
    print(f"Request: {request}  (agent model: {AGENT_MODEL})")
    print(f"\nAnswer: {run(request)}")
    print(f"Audit log (what really changed): {AUDIT_LOG or 'nothing'}")
