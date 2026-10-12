"""Lab 2, Exercise 2: an AI assistant that calls application functions: search the catalogue,
retrieve the learner's information, check an enrolment's status and create a support ticket.
The model asks for a function; this code decides whether and how it runs.
Run:  python l2_tools.py "Which beginner courses cost less than $300?" """
import json
import sys
import uuid
from pathlib import Path

from client import AGENT_MODEL, get_client

COURSES = json.loads((Path(__file__).parent / "data" / "courses.json").read_text(encoding="utf-8"))
LEARNERS = {"L-MEI": {"name": "Mei Chen", "country": "Singapore", "enrolments": ["TC-10293", "TC-10477"]}}
ENROLMENTS = {"TC-10293": {"course": "AI-102: Azure AI Engineer", "status": "completed", "certificate": "issued"},
              "TC-10477": {"course": "Building RAG Applications", "status": "confirmed", "starts_in_days": 10}}
SIGNED_IN = "L-MEI"            # the app knows who is signed in; the model never chooses this


# ---------------- the application functions (plain Python)
def search_courses(text: str = "", level: str | None = None, max_price_usd: int | None = None):
    # Models sometimes send numbers as text ("300"): accept them, like any API that faces untrusted input.
    max_price_usd = int(float(max_price_usd)) if max_price_usd not in (None, "") else None
    hits = [c for c in COURSES if (not level or c["level"] == level)
            and (max_price_usd is None or c["price_usd"] <= max_price_usd)
            and (not text or text.lower() in (c["title"] + " " + c["description"]).lower())]
    return [{k: c[k] for k in ("id", "title", "level", "price_usd")} for c in hits[:5]]


def get_my_profile():
    me = LEARNERS[SIGNED_IN]
    return {**me, "enrolments": [{"enrolment_id": e, "course": ENROLMENTS[e]["course"]} for e in me["enrolments"]]}


def check_enrolment_status(enrolment_id: str):
    if enrolment_id not in LEARNERS[SIGNED_IN]["enrolments"]:
        return {"error": "not one of the signed-in learner's enrolments; call get_my_profile to see them"}
    return ENROLMENTS[enrolment_id]


def create_support_ticket(summary: str, category: str):
    return {"ticket_id": "T-" + uuid.uuid4().hex[:6].upper(), "status": "created", "category": category}


FUNCTIONS = {f.__name__: f for f in (search_courses, get_my_profile, check_enrolment_status, create_support_ticket)}

# ---------------- how the model sees them (JSON Schema)
TOOLS = [
    {"type": "function", "function": {
        "name": "search_courses", "description": "Search the TrainCrest course catalogue by keyword, level and maximum price.",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string", "description": "One keyword, e.g. 'azure' or 'python'; empty for any"},
            "level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
            "max_price_usd": {"type": "integer", "description": "Highest price in US dollars"}}}}},
    {"type": "function", "function": {
        "name": "get_my_profile", "description": "The signed-in learner's name, country, and enrolments with course names.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "check_enrolment_status", "description": "Status of one of the signed-in learner's enrolments.",
        "parameters": {"type": "object", "properties": {
            "enrolment_id": {"type": "string", "description": "Like TC-12345, from get_my_profile"}},
            "required": ["enrolment_id"]}}},
    {"type": "function", "function": {
        "name": "create_support_ticket", "description": "Create a ticket for the human support team.",
        "parameters": {"type": "object", "properties": {
            "summary": {"type": "string"},
            "category": {"type": "string", "enum": ["billing", "scheduling", "lab_access", "other"]}},
            "required": ["summary", "category"]}}},
]


def ask(question: str, max_rounds: int = 5) -> str:
    client = get_client()
    messages = [{"role": "system", "content": "You are Traincrest Assist. Use the tools for facts; never guess IDs. "
                                              "The learner can't call functions: call them yourself, starting with "
                                              "get_my_profile when you need an enrolment ID. Answer in at most 60 words."},
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
    questions = sys.argv[1:] or ["Which beginner courses cost less than $300?",
                                 "What's the status of my RAG course?",
                                 "My invoice is wrong, please open a ticket for me."]
    for q in questions:
        print(f"Q: {q}")
        print(f"A: {ask(q)}\n")
