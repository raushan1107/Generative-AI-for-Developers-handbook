"""Drill 01.6 (reference solution): estimate tokens and cost for a text file,
and check whether it fits a model's context window."""
import argparse
import sys
from pathlib import Path

import tiktoken


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate tokens and cost for a text file.")
    parser.add_argument("file", help="path to a text file")
    parser.add_argument("--window", type=int, default=128_000, help="context window in tokens")
    parser.add_argument("--reserve", type=int, default=4_000, help="tokens reserved for the answer")
    parser.add_argument("--price-in", type=float, default=0.40, help="USD per 1M input tokens")
    args = parser.parse_args()

    text = Path(args.file).read_text(encoding="utf-8")
    tokens = len(tiktoken.get_encoding("o200k_base").encode(text))
    budget = args.window - args.reserve
    fits = tokens <= budget

    print(f"{args.file}: {len(text):,} characters, ~{tokens:,} tokens (o200k_base estimate)")
    print(f"Input cost per call: ~${tokens * args.price_in / 1_000_000:.4f}")
    print(f"Fits a {args.window:,}-token window with {args.reserve:,} reserved for output: "
          f"{'yes' if fits else 'NO'} ({tokens / budget:.0%} of the input budget)")
    return 0 if fits else 1


if __name__ == "__main__":
    sys.exit(main())
