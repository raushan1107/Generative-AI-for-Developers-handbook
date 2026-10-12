"""Drill 03.4: verify an AI-generated test set before you trust it."""
import json
import sys
from collections import Counter
from pathlib import Path

from tickets import CATEGORIES, TEST_TICKETS

path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/eval_tickets.json")
rows = json.loads(path.read_text(encoding="utf-8"))
problems = []

for i, row in enumerate(rows):
    if set(row) != {"text", "label"}:
        problems.append(f"row {i}: keys should be text and label, got {sorted(row)}")
    elif row["label"] not in CATEGORIES:
        problems.append(f"row {i}: unknown label {row['label']!r}")
    elif not row["text"].strip():
        problems.append(f"row {i}: empty text")

texts = [r.get("text", "").strip().lower() for r in rows]
dupes = [t for t, n in Counter(texts).items() if n > 1]
if dupes:
    problems.append(f"{len(dupes)} duplicate texts, e.g. {dupes[0]!r}")

test_texts = {t.lower() for t, _ in TEST_TICKETS}
leaked = [t for t in texts if t in test_texts]
if leaked:
    problems.append(f"{len(leaked)} rows copy the fixed test tickets (that would inflate scores)")

counts = Counter(r.get("label") for r in rows)
print(f"{len(rows)} rows · labels: " + ", ".join(f"{c}={counts.get(c, 0)}" for c in CATEGORIES))
non_english = sum(1 for t in texts if any(ord(ch) > 127 for ch in t))
print(f"rows with non-ASCII text (other languages, accents): {non_english}")
if min(counts.get(c, 0) for c in CATEGORIES) < 3:
    problems.append("every category needs at least 3 examples")

print("\n".join(problems) if problems else "OK: the dataset passes all checks")
sys.exit(1 if problems else 0)
