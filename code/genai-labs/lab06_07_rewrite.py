"""Drill 06.7: rewrite follow-up questions before retrieving.
'And how much is it after that?' means nothing to a search index. Ask the model to turn the last
message into a standalone question using the conversation, then retrieve with that."""
from kb_index import load_or_build
from llm import MODEL, get_client

CONVERSATIONS = [
    [("user", "How long do labs stay open after my course?"),
     ("assistant", "Labs stay open for 30 days after the course ends, and you can ask for one free 7-day extension."),
     ("user", "And after that, how much is it?")],
    [("user", "I want to cancel my AZ-104 course."),
     ("assistant", "I can help. How many days are left before it starts?"),
     ("user", "ten days. what do i get back?")],
    [("user", "My certificate came with my old surname."),
     ("assistant", "Sorry about that! When was it issued?"),
     ("user", "about two months ago, does it cost anything?")],
]

REWRITE = """Rewrite the user's last message as one standalone question that can be understood without
the conversation. Keep their meaning and details; add the missing subject from the conversation.
Return only the question.

Conversation:
{history}"""

index = load_or_build()
client = get_client()


def top(question):
    hits = index.search(question, k=2)
    return ", ".join(f"{h['title']} ({h['score']:.2f})" for h in hits)


for conversation in CONVERSATIONS:
    history = "\n".join(f"{role}: {text}" for role, text in conversation)
    last = conversation[-1][1]
    rewritten = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": REWRITE.format(history=history)}]
    ).choices[0].message.content.strip()
    print(f"Follow-up : {last}\n  retrieves: {top(last)}")
    print(f"Rewritten : {rewritten}\n  retrieves: {top(rewritten)}\n")
