"""Drill 07.3: tool design decides tool choice. The same 8 requests, two tool sets with the same
functions: one with terse names and no descriptions, one written for a model to read.
Count how often the model's first call is the right tool."""
from desk import TODAY
from desk_tools import kit
from llm import MODEL, get_client
from llm_tools import TOOL_EXTRAS

CLEAR = kit.schemas()
TERSE_NAMES = {"my_cards": "crd", "card_status": "cst", "recent_transactions": "txn", "dispute_quote": "dq",
               "freeze_card": "frz", "open_dispute": "dsp", "create_case": "cs"}


def terse(tool):
    """Same function, written the way many internal APIs are: short names, no descriptions."""
    f = tool["function"]
    params = {"type": "object", "properties": {f"p{i}": {"type": "string"} for i in range(len(f["parameters"]["properties"]))},
              "required": [f"p{i}" for i in range(len(f["parameters"]["properties"]))], "additionalProperties": False}
    return {"type": "function", "function": {"name": TERSE_NAMES[f["name"]], "description": "", "parameters": params}}


TERSE = [terse(t) for t in CLEAR]
REQUESTS = [
    ("Is my card ending 4821 active or frozen?", "card_status"),
    ("Show me the recent payments on my card ending 4821.", "recent_transactions"),
    ("Can I still dispute payment TX-1006, and when would I get the money?", "dispute_quote"),
    ("Freeze my card ending 1177 right now.", "freeze_card"),
    ("Open a dispute for TX-1002, I was charged twice.", "open_dispute"),
    ("Which cards do I have?", "my_cards"),
    ("I want to complain about how a branch employee treated me.", "create_case"),
    ("Has my debit card ending 1177 been frozen?", "card_status"),
]
client = get_client()
system = f"You act for an RR Finance Bank customer. Today is {TODAY}. Call exactly one tool for the request."

for label, tools, names in (("terse", TERSE, TERSE_NAMES), ("clear", CLEAR, {k: k for k in TERSE_NAMES})):
    right = 0
    for request, expected in REQUESTS:
        msg = client.chat.completions.create(
            model=MODEL, tools=tools, parallel_tool_calls=False, **TOOL_EXTRAS,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": request}]).choices[0].message
        got = msg.tool_calls[0].function.name if msg.tool_calls else "(no tool)"
        ok = got == names[expected]
        right += ok
        print(f"  [{label}] {'✓' if ok else '✗'} {request[:52]:52} -> {got}")
    print(f"{label.upper()} tools: {right}/{len(REQUESTS)} right first call\n")
