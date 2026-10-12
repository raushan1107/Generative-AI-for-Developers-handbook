"""Drill 04.1: why free text breaks your code.
We ask for a course recommendation and try to pull the price out with a regex,
the way a quick prototype would. Run with --offline to use three saved replies."""
import re
import sys

QUESTION = """A learner wants a beginner Python course under $300.
Recommend one course from this list and say its price.
- C101 Python Foundations, beginner, $290
- C114 Docker Quick Start, beginner, $190
- C103 Machine Learning Essentials, intermediate, $1190"""

# Three real-looking replies to the same question. All are fine for a human reader.
SAVED_REPLIES = [
    "I recommend Python Foundations (C101). It costs $290 and is designed for complete beginners.",
    "Python Foundations is the best fit. If budget is tight, Docker Quick Start is only $190, "
    "but Python Foundations at $290 teaches programming from zero.",
    "Go for **Python Foundations**: beginner level, 290 USD, five days.",
]


def parse_price(reply: str):
    """The 'quick prototype' parser: first dollar amount in the text."""
    match = re.search(r"\$(\d+)", reply)
    return int(match.group(1)) if match else None


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
        price = parse_price(reply)
        verdict = "OK" if price == 290 else ("WRONG" if price else "FAILED")
        print(f"Reply {i}: {reply[:70]}{'...' if len(reply) > 70 else ''}")
        print(f"  parsed price -> {price}   {verdict}\n")
