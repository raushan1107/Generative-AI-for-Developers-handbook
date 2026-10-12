"""Drill 03.10: run the messy prompt and your structured rewrite on the same messages, with simple checks."""
import sys
from pathlib import Path
from string import Template

from llm import get_client, MODEL

client = get_client()

MESSAGES = [
    "My lab expired yesterday and I still have the final project to do. Help!",
    "I already used my free extension, can I get more lab time? Or a refund for the lab days I missed?",
    "Where is my exam voucher?",
]


def checks(reply, message):
    """Cheap automatic checks. They don't prove quality, but they catch the obvious failures."""
    words = len(reply.split())
    results = [("under 90 words", words < 90), ("no refund promised", "refund" not in reply.lower()
                                                or "no refund" in reply.lower() or "not offer" in reply.lower())]
    if "voucher" in message.lower():
        results.append(("hands off non-lab topics", "team" in reply.lower()))
    if "free extension" in message.lower():
        results.append(("mentions the $49 option", "49" in reply))
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
