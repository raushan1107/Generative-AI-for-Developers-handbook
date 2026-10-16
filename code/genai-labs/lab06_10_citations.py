"""Drill 06.10: check four answers to the same question against the sources the model was given.
Offline: the answers are written out here, so you can see exactly what each check catches."""
from citations import check, render

QUESTION = "My card was stolen this morning. How fast can I get a new one, and do I pay for payments the thief made?"
SOURCES = [
    {"title": "Lost or stolen cards > Report it and get a replacement", "source": "lost-stolen-cards.md",
     "text": "We cancel the card permanently and send a replacement with a new number within 5 to 7 business days. "
             "Express delivery within 2 business days costs $15, and is free for Premier Checking customers."},
    {"title": "Lost or stolen cards > Your liability", "source": "lost-stolen-cards.md",
     "text": "You pay nothing for payments you didn't make if you report the card within 2 business days of "
             "noticing it is missing."},
]
ANSWERS = {
    "grounded": "A new card arrives within 5 to 7 business days, or in 2 business days for $15 [1]. "
                "You pay nothing for payments you didn't make, because you're reporting it within 2 business days [2].",
    "invented citation": "A new card arrives within 5 to 7 business days [1]. You pay nothing for the thief's payments [4].",
    "number without a source": "A new card arrives within 5 to 7 business days [1]. We'll refund the payments within 10 business days.",
    "number not in its source": "Express delivery costs $25 [1]. You pay nothing for payments you didn't make [2].",
}

for name, text in ANSWERS.items():
    report = check(text, SOURCES, QUESTION)
    problems = {k: v for k, v in report.items() if v and k not in ("ok", "cited")}
    print(f"{name.upper()}: {'OK' if report['ok'] else problems}")
print("\nRendered for the customer (grounded answer):\n")
print(render(ANSWERS["grounded"], SOURCES, check(ANSWERS["grounded"], SOURCES, QUESTION)))
