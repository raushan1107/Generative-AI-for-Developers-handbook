"""Drills 03.5 and 03.6: zero-shot vs few-shot triage of bank tickets, scored against labels.

  python lab03_05_triage.py --mode zero              # 03.5: zero-shot baseline
  python lab03_05_triage.py --mode few               # 03.6: with examples
  python lab03_05_triage.py --mode both --data data/eval_tickets.json
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from llm import get_client, MODEL
from tickets import CATEGORIES, FEW_SHOT_EXAMPLES, TEST_TICKETS

INSTRUCTIONS = (f"Classify the RR Finance Bank customer message into exactly one category: "
                f"{', '.join(CATEGORIES)}. Reply with the category only, in lowercase.")

client = get_client()


def classify(ticket, few_shot):
    messages = [{"role": "system", "content": INSTRUCTIONS}]
    if few_shot:
        for text, label in FEW_SHOT_EXAMPLES:          # examples as user/assistant pairs
            messages += [{"role": "user", "content": text}, {"role": "assistant", "content": label}]
    messages.append({"role": "user", "content": ticket})
    r = client.chat.completions.create(model=MODEL, messages=messages)
    return r.choices[0].message.content.strip().lower(), r.usage.prompt_tokens


def evaluate(dataset, few_shot):
    print("\n===== FEW-SHOT =====" if few_shot else "\n===== ZERO-SHOT =====")
    correct, off_list, tokens, mistakes = 0, 0, 0, Counter()
    for ticket, expected in dataset:
        got, used = classify(ticket, few_shot)
        tokens += used
        correct += got == expected
        off_list += got not in CATEGORIES
        if got != expected:
            mistakes[f"{expected} -> {got}"] += 1
        print(f" {'✓' if got == expected else '✗'} {got:13} (expected {expected:12}) {ticket[:48]}")
    n = len(dataset)
    print(f"Accuracy {correct}/{n} ({correct / n:.0%}) · off-list labels: {off_list} · "
          f"avg input tokens: {tokens // n}")
    if mistakes:
        print("Most common mistakes:", ", ".join(f"{k} x{v}" for k, v in mistakes.most_common(3)))


parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["zero", "few", "both"], default="both")
parser.add_argument("--data", help="optional JSON file of {text, label} rows instead of the 12 fixed tickets")
args = parser.parse_args()

data = TEST_TICKETS
if args.data:
    data = [(r["text"], r["label"]) for r in json.loads(Path(args.data).read_text(encoding="utf-8"))]

if args.mode in ("zero", "both"):
    evaluate(data, few_shot=False)
if args.mode in ("few", "both"):
    evaluate(data, few_shot=True)
