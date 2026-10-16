"""Drill 04.1: why free text breaks your code.
We ask which card matches a customer's need and try to pull the APR out with a regex,
the way a quick prototype would. Run with --offline to use three saved replies."""
import re
import sys

QUESTION = """A customer wants a credit card with no annual fee and the lowest APR.
Which card on this list matches? Name it and say its APR.
- P110 Cashback Card, no annual fee, 22.99% APR
- P111 Voyager Travel Card, $95 annual fee, 24.49% APR
- P112 Starter Credit Card, no annual fee, 26.99% APR"""

# Three real-looking replies to the same question. All are fine for a human reader.
SAVED_REPLIES = [
    "The Cashback Card (P110) matches: no annual fee and a 22.99% APR.",
    "Both the Starter Credit Card (26.99% APR) and the Cashback Card have no annual fee, "
    "so the Cashback Card at 22.99% is the better match.",
    "Go for the **Cashback Card**: no annual fee, APR of 22.99 percent.",
]


def parse_apr(reply: str):
    """The 'quick prototype' parser: first percentage in the text."""
    match = re.search(r"(\d+(?:\.\d+)?)\s?%", reply)
    return float(match.group(1)) if match else None


def get_replies():
    if "--offline" in sys.argv:
        return SAVED_REPLIES
    from llm import MODEL, get_client
    client = get_client()
    replies = []
    for _ in range(3):
        r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": QUESTION}])
        replies.append(r.choices[0].message.content or "")
    return replies


if __name__ == "__main__":
    for i, reply in enumerate(get_replies(), 1):
        apr = parse_apr(reply)
        verdict = "OK" if apr == 22.99 else ("WRONG" if apr else "FAILED")
        print(f"Reply {i}: {reply[:70]}{'...' if len(reply) > 70 else ''}")
        print(f"  parsed APR -> {apr}   {verdict}\n")
