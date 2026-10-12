"""Drill 07.3: tool design decides tool choice. The same 8 requests, two tool sets with the same
functions: one with terse names and no descriptions, one written for a model to read.
Count how often the model's first call is the right tool."""
from desk import TODAY, upcoming_sessions
from desk_tools import kit
from llm import MODEL, get_client
from llm_tools import TOOL_EXTRAS

CLEAR = kit.schemas()
TERSE_NAMES = {"my_enrolments": "enr", "lab_status": "lab", "upcoming_sessions": "sess", "reschedule_quote": "quote",
               "extend_lab": "ext", "reschedule": "move", "create_ticket": "tkt"}


def terse(tool):
    """Same function, written the way many internal APIs are: short names, no descriptions."""
    f = tool["function"]
    params = {"type": "object", "properties": {f"p{i}": {"type": "string"} for i in range(len(f["parameters"]["properties"]))},
              "required": [f"p{i}" for i in range(len(f["parameters"]["properties"]))], "additionalProperties": False}
    return {"type": "function", "function": {"name": TERSE_NAMES[f["name"]], "description": "", "parameters": params}}


TERSE = [terse(t) for t in CLEAR]
REQUESTS = [
    ("What's the status of my lab for TC-10293?", "lab_status"),
    ("Which start dates are available for course C110?", "upcoming_sessions"),
    ("Can I still move TC-20877, and how much would it cost?", "reschedule_quote"),
    ("Please use my free lab extension on TC-10293.", "extend_lab"),
    (f"Move TC-20877 to the session on {upcoming_sessions('C110')[1]}.", "reschedule"),
    ("What am I enrolled in?", "my_enrolments"),
    ("I want to complain about my trainer's behaviour.", "create_ticket"),
    ("Is my sandbox for TC-31002 still running, and until when?", "lab_status"),
]
client = get_client()
system = f"You act for a TrainCrest learner. Today is {TODAY}. Call exactly one tool for the request."

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
