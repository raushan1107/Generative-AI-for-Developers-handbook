"""Lab 2, Exercise 2: an AI assistant that calls application functions: search the product catalogue,
retrieve the customer's information, check a card's status and create a support case.
The model asks for a function; this code decides whether and how it runs.
Run:  python l2_tools.py "Which cards have no annual fee?" """
import json
import sys
import uuid
from pathlib import Path

from client import AGENT_MODEL, get_client

PRODUCTS = json.loads((Path(__file__).parent / "data" / "products.json").read_text(encoding="utf-8"))
CUSTOMERS = {"RR-10293": {"name": "Mei Chen", "country": "Singapore", "cards": ["4821", "1177"]}}
CARDS = {"4821": {"product": "Cashback Card", "status": "active"},
         "1177": {"product": "Everyday Checking debit card", "status": "replacement sent", "arrives_in_days": 4}}
SIGNED_IN = "RR-10293"         # the app knows who is signed in; the model never chooses this


# ---------------- the application functions (plain Python)
def search_products(text: str = "", family: str | None = None, max_annual_fee_usd: int | None = None):
    # Models sometimes send numbers as text ("100"): accept them, like any API that faces untrusted input.
    max_annual_fee_usd = int(float(max_annual_fee_usd)) if max_annual_fee_usd not in (None, "") else None
    hits = [p for p in PRODUCTS if (not family or p["family"] == family)
            and (max_annual_fee_usd is None or p["annual_fee_usd"] <= max_annual_fee_usd)
            and (not text or text.lower() in (p["name"] + " " + p["description"]).lower())]
    return [{k: p[k] for k in ("id", "name", "family", "annual_fee_usd", "rate_pct", "rate_type")} for p in hits[:5]]


def get_my_profile():
    me = CUSTOMERS[SIGNED_IN]
    return {**me, "cards": [{"card_last4": c, "product": CARDS[c]["product"]} for c in me["cards"]]}


def check_card_status(card_last4: str):
    if card_last4 not in CUSTOMERS[SIGNED_IN]["cards"]:
        return {"error": "not one of the signed-in customer's cards; call get_my_profile to see them"}
    return CARDS[card_last4]


def create_support_case(summary: str, category: str):
    return {"case_id": "CS-" + uuid.uuid4().hex[:6].upper(), "status": "created", "category": category}


FUNCTIONS = {f.__name__: f for f in (search_products, get_my_profile, check_card_status, create_support_case)}

# ---------------- how the model sees them (JSON Schema)
TOOLS = [
    {"type": "function", "function": {
        "name": "search_products", "description": "Search the RR Finance Bank product catalogue by keyword, family and maximum annual fee.",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string", "description": "One keyword, e.g. 'travel' or 'savings'; empty for any"},
            "family": {"type": "string", "enum": ["accounts", "cards", "loans"]},
            "max_annual_fee_usd": {"type": "integer", "description": "Highest annual fee in US dollars"}}}}},
    {"type": "function", "function": {
        "name": "get_my_profile", "description": "The signed-in customer's name, country, and cards (last four digits and product).",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "check_card_status", "description": "Status of one of the signed-in customer's cards.",
        "parameters": {"type": "object", "properties": {
            "card_last4": {"type": "string", "description": "Last four digits, like 4821, from get_my_profile"}},
            "required": ["card_last4"]}}},
    {"type": "function", "function": {
        "name": "create_support_case", "description": "Create a case for the human support team.",
        "parameters": {"type": "object", "properties": {
            "summary": {"type": "string"},
            "category": {"type": "string", "enum": ["card", "dispute", "fraud", "fees", "other"]}},
            "required": ["summary", "category"]}}},
]


def ask(question: str, max_rounds: int = 5) -> str:
    client = get_client()
    messages = [{"role": "system", "content": "You are RR Finance Assist. Use the tools for facts; never guess IDs, "
                                              "fees or rates. The customer can't call functions: call them yourself, "
                                              "starting with get_my_profile when you need a card. Never ask for a "
                                              "full card number or PIN. Answer in at most 60 words."},
                {"role": "user", "content": question}]
    for _ in range(max_rounds):
        msg = client.chat.completions.create(model=AGENT_MODEL, messages=messages, tools=TOOLS).choices[0].message
        if not msg.tool_calls:
            return msg.content.strip()
        messages.append(msg)
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            func = FUNCTIONS.get(call.function.name)
            try:
                result = func(**args) if func else {"error": f"unknown function {call.function.name}"}
            except TypeError as e:                       # wrong or missing arguments
                result = {"error": f"bad arguments: {e}"}
            print(f"  -> {call.function.name}({args}) = {json.dumps(result)[:90]}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
    return "Sorry, that took too many steps."


if __name__ == "__main__":
    questions = sys.argv[1:] or ["Which cards have no annual fee?",
                                 "Has the replacement for my debit card been sent?",
                                 "I was charged a fee I don't understand, please open a case for me."]
    for q in questions:
        print(f"Q: {q}")
        print(f"A: {ask(q)}\n")
