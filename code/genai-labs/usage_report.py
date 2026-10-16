"""Drill 02.15 (reference solution): summarise usage.jsonl by label and project a monthly bill."""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Summarise LLM usage from a JSON-lines log.")
    parser.add_argument("log", nargs="?", default="usage.jsonl")
    parser.add_argument("--turns-per-month", type=int, default=160_000)
    args = parser.parse_args()

    totals = defaultdict(lambda: {"calls": 0, "in": 0, "out": 0, "cost": 0.0})
    for line in Path(args.log).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        t = totals[row.get("label", "unlabelled")]
        t["calls"] += 1
        t["in"] += row.get("tokens_in", 0)
        t["out"] += row.get("tokens_out", 0)
        t["cost"] += row.get("cost_usd", 0.0)

    print(f"{'label':26} {'calls':>5} {'avg in':>8} {'avg out':>8} {'avg $/call':>11} {'$/month':>10}")
    for label, t in sorted(totals.items(), key=lambda kv: -kv[1]["cost"] / kv[1]["calls"]):
        avg_cost = t["cost"] / t["calls"]
        print(f"{label:26} {t['calls']:>5} {t['in'] // t['calls']:>8} {t['out'] // t['calls']:>8} "
              f"{avg_cost:>11.5f} {avg_cost * args.turns_per_month:>10,.0f}")


if __name__ == "__main__":
    main()
