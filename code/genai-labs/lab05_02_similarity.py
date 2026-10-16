"""Drill 05.2: similarity by hand, then on real embeddings.
Run:  python lab05_02_similarity.py --toy   (offline, tiny 2-D vectors)
      python lab05_02_similarity.py         (real embeddings)"""
import sys

from similarity import cosine, cosine_matrix, dot, euclidean

if "--toy" in sys.argv:
    # Pretend dimension 1 = "about getting money back", dimension 2 = "about a missing card".
    dispute = [0.9, 0.1]
    money_back = [0.8, 0.2]
    money_back_long = [1.6, 0.4]          # same direction, twice as long
    stolen_card = [0.1, 0.9]
    for name, v in [("money_back", money_back), ("money_back_long", money_back_long), ("stolen_card", stolen_card)]:
        print(f"dispute vs {name:<16} cosine={cosine(dispute, v):.3f}  dot={dot(dispute, v):.3f}  "
              f"euclidean={euclidean(dispute, v):.3f}")
    raise SystemExit

from embed import embed  # noqa: E402  (only needed for the live part)

SENTENCES = [
    "How do I get my money back?",
    "Can I dispute a double charge?",
    "¿Cómo puedo reclamar un cargo?",
    "My card was stolen.",
    "Someone took my wallet.",
    "What's the weather in Paris?",
]
LABELS = ["money", "dispute", "reclamar", "stolen", "wallet", "weather"]

m = cosine_matrix(embed(SENTENCES))
print(" " * 10 + "".join(f"{label:>10}" for label in LABELS))
for label, row in zip(LABELS, m):
    print(f"{label:<10}" + "".join(f"{x:>10.2f}" for x in row))
