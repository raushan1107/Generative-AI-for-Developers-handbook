"""Drill 05.9: keyword vs vector vs hybrid on the help-centre sections.
Each query has the section that should come first. Which method gets it?"""
from chunkers import by_headings, load_articles
from embed import embed
from hybrid import bm25_ranking, rrf, vector_ranking

TESTS = {                                   # query -> heading of the section that answers it
    "safe account": "We will never ask",
    "what costs $45?": "Limits and fees",
    "4 pm cut-off": "Timing",
    "provisional credit": "What happens next",
    "Is there a fee if I'm only $30 overdrawn?": "Overdrafts",
    "can I log in with my fingerprint?": "Signing in",
    "I paid the wrong person, can you get it back?": "Sent money to the wrong person",
    "cryptocurrency trading": None,         # nothing in the help centre answers this
}

sections = [text for md in load_articles().values() for text in by_headings(md)]
headings = [s.split("\n")[0].split(" > ")[-1] for s in sections]
vectors = embed(sections)
top1 = {"keyword": 0, "vector": 0, "hybrid": 0}
top3 = dict(top1)

for query, expected in TESTS.items():
    rankings = {"keyword": bm25_ranking(query, sections), "vector": vector_ranking(embed([query])[0], vectors)}
    rankings["hybrid"] = rrf([rankings["keyword"], rankings["vector"]])
    print(f"\n{query!r}  (want: {expected or 'no match'})")
    for method, ranking in rankings.items():
        first3 = [headings[i] for i in ranking[:3]]
        top = first3[0] if first3 else None
        ok1 = top == expected
        ok3 = expected in first3 if expected else not first3
        top1[method] += ok1
        top3[method] += ok3
        print(f"  {method:<8} {'OK  ' if ok1 else 'MISS'} {top or '(no match)':<26} in top 3: {'yes' if ok3 else 'no'}")

print("\nRight section first: ", ", ".join(f"{m} {n}/{len(TESTS)}" for m, n in top1.items()))
print("Right section in top 3:", ", ".join(f"{m} {n}/{len(TESTS)}" for m, n in top3.items()))
