"""Drill 06.7: rewrite follow-up questions before retrieving.
'And how much is it after that?' means nothing to a search index. Ask the model to turn the last
message into a standalone question using the conversation, then retrieve with that."""
from kb_index import load_or_build
from llm import MODEL, get_client

CONVERSATIONS = [
    [("user", "My card was stolen yesterday."),
     ("assistant", "I'm sorry. Freeze it in the app first; a replacement arrives in 5 to 7 business days."),
     ("user", "And if I need it faster, how much is that?")],
    [("user", "I want to take money out of my 12-month CD."),
     ("assistant", "I can help. Is it before the CD matures?"),
     ("user", "yes, three months early. what do i lose?")],
    [("user", "I sent $300 to the wrong account by mistake."),
     ("assistant", "Sorry to hear that! Was it a wire or a standard transfer?"),
     ("user", "a wire, yesterday. can you still cancel it?")],
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
