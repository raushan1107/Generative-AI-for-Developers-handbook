"""Drill 03.10: run the messy prompt and your structured rewrite on the same messages, with simple checks."""
import re
import sys
from pathlib import Path
from string import Template

from llm import get_client, MODEL

client = get_client()

MESSAGES = [
    "I lost my debit card last night and I'm abroad until Friday. Help!",
    "Can you send my new card express? How much does that cost? I'm on Everyday Checking.",
    "What is the interest rate on a personal loan?",
]

SECRET = re.compile(r"\b(?:pin|password|card number)\b", re.I)


def asks_for_secrets(reply):
    """True if a sentence mentions a PIN, password or card number without saying 'never' or 'don't'."""
    sentences = re.split(r"(?<=[.!?])\s+", reply)
    return any(SECRET.search(s) and not re.search(r"\b(?:never|don't|do not|won't)\b", s, re.I) for s in sentences)


def checks(reply, message):
    """Cheap automatic checks. They don't prove quality, but they catch the obvious failures."""
    words = len(reply.split())
    results = [("under 90 words", words < 90), ("never asks for a PIN or card number", not asks_for_secrets(reply))]
    if "loan" in message.lower():
        results.append(("hands off non-card topics", "team" in reply.lower()))
        results.append(("doesn't invent a rate", not re.search(r"\d+(?:\.\d+)?\s?%", reply)))
    if "express" in message.lower():
        results.append(("mentions the $15 fee", "15" in reply))
        results.append(("doesn't waive it for Everyday Checking", not re.search(r"\b(?:free|waived?)\b", reply, re.I)))
    return words, results


files = sys.argv[1:] or ["messy_prompt.txt", "structured_prompt.txt"]
for name in files:
    template = Template(Path(name).read_text(encoding="utf-8"))
    print(f"\n==================== {name} ====================")
    passed = total = 0
    for message in MESSAGES:
        r = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": template.substitute(message=message)}])
        reply = r.choices[0].message.content.strip()
        words, results = checks(reply, message)
        passed += sum(ok for _, ok in results)
        total += len(results)
        print(f"\n> {message}\n{reply}\n  [{words} words] " +
              "  ".join(f"{'PASS' if ok else 'FAIL'}: {label}" for label, ok in results))
    print(f"\n{name}: {passed}/{total} checks passed")
