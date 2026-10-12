"""Lab 3, Exercise 2: an agent that understands a request, selects and calls tools, processes the
results and returns a final answer. Changes need the learner's approval (you type y or n).
Run:  python l3_agent.py "Please extend my AI-102 lab and tell me the new end date." """
import json
import sys
from datetime import date, timedelta

from client import AGENT_MODEL, get_client

TODAY = date.today()
LEARNER = "Mei"                                       # the signed-in learner: set by the app, not the model
ENROLMENTS = {"TC-10293": {"course": "AI-102: Azure AI Engineer", "lab_until": TODAY + timedelta(days=4),
                           "free_extension_used": False},
              "TC-10477": {"course": "Building RAG Applications", "lab_until": None, "free_extension_used": False}}
AUDIT_LOG = []                                        # every real change, in order


# ---------------- tools: two reads, one write
def my_enrolments():
    return [{"enrolment_id": k, "course": v["course"]} for k, v in ENROLMENTS.items()]


def lab_status(enrolment_id):
    e = ENROLMENTS.get(enrolment_id)
    if e is None:
        return {"error": f"{enrolment_id} is not one of {LEARNER}'s enrolments; call my_enrolments yourself"}
    if e["lab_until"] is None:
        return {"enrolment_id": enrolment_id, "lab": "not started yet"}
    return {"enrolment_id": enrolment_id, "lab_until": e["lab_until"].isoformat(),
            "free_extension_available": not e["free_extension_used"]}


def extend_lab(enrolment_id):
    e = ENROLMENTS.get(enrolment_id)
    if e is None or e["lab_until"] is None or e["free_extension_used"]:
        return {"error": "no free extension available for this enrolment; offer a support ticket"}
    e["lab_until"] += timedelta(days=7)
    e["free_extension_used"] = True
    AUDIT_LOG.append({"action": "extend_lab", "enrolment_id": enrolment_id, "lab_until": e["lab_until"].isoformat()})
    return {"enrolment_id": enrolment_id, "lab_until": e["lab_until"].isoformat(), "fee_usd": 0}


FUNCTIONS = {"my_enrolments": my_enrolments, "lab_status": lab_status, "extend_lab": extend_lab}
NEEDS_APPROVAL = {"extend_lab"}


def tool(name, description, properties=None):
    params = {"type": "object", "properties": properties or {}, "required": list(properties or {})}
    return {"type": "function", "function": {"name": name, "description": description, "parameters": params}}


ID = {"enrolment_id": {"type": "string", "description": "Like TC-12345, from my_enrolments"}}
TOOLS = [tool("my_enrolments", "List the signed-in learner's enrolments with their IDs."),
         tool("lab_status", "Lab end date for one enrolment and whether the free extension is available.", ID),
         tool("extend_lab", "Use the free 7-day lab extension. Changes the booking; the learner must approve.", ID)]
SYSTEM = (f"You are Traincrest Assist acting for the signed-in learner, {LEARNER}. Today is {TODAY}. "
          "Use tools for every fact and action; never guess IDs or dates. The learner can't call tools; "
          "call them yourself, starting with my_enrolments. If an action is declined, don't retry it. "
          "Finish with a short answer saying what was done.")


def approve(name, args):
    """A person decides. The preview comes from the real data, not from the model."""
    status = lab_status(args.get("enrolment_id", ""))
    print(f"\n  APPROVAL NEEDED: extend {args.get('enrolment_id')} by 7 days, free "
          f"(lab currently open until {status.get('lab_until')})")
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
                result = {"error": "the learner declined this action"}
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
    request = sys.argv[1] if len(sys.argv) > 1 else "Please extend my AI-102 lab and tell me the new end date."
    print(f"Request: {request}  (agent model: {AGENT_MODEL})")
    print(f"\nAnswer: {run(request)}")
    print(f"Audit log (what really changed): {AUDIT_LOG or 'nothing'}")
