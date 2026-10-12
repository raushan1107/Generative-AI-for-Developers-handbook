"""Reliability check for triage: run it before every prompt or model change.

From the project folder:   python -m tests.check_triage            (calls the real model)
                           python -m tests.check_triage --min-accuracy 0.9
Exit code 0 = pass, 1 = fail, so a CI pipeline can block a bad change (Module 12).
"""
import argparse
import json
import sys
from pathlib import Path

from app.llm import get_client
from app.triage import TriageError, triage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/eval_tickets.json")
    parser.add_argument("--min-accuracy", type=float, default=0.85)
    args = parser.parse_args()

    rows = json.loads(Path(args.data).read_text(encoding="utf-8"))
    client = get_client()
    valid = correct = repaired = 0
    version = "?"
    for row in rows:
        try:
            result, version, attempts = triage(client, row["text"])
        except TriageError as e:
            print(f"  INVALID {row['text'][:50]}  ({e})")
            continue
        valid += 1
        repaired += attempts > 1
        ok = result.issue_category == row["label"]
        correct += ok
        print(f"  {'✓' if ok else '✗'} {result.issue_category:13} expected {row['label']:13} {row['text'][:44]}")

    n = len(rows)
    accuracy = correct / n
    print(f"\nprompt {version}: valid {valid}/{n} · repaired {repaired} · accuracy {correct}/{n} ({accuracy:.0%})")
    if valid < n or accuracy < args.min_accuracy:
        print(f"FAIL (needs 100% valid and at least {args.min_accuracy:.0%} accuracy)")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
