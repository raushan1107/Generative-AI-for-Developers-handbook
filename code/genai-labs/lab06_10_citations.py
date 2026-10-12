"""Drill 06.10: check four answers to the same question against the sources the model was given.
Offline: the answers are written out here, so you can see exactly what each check catches."""
from citations import check, render

QUESTION = "I need to move my course, it starts in 3 days. What does it cost, and can I get money back instead?"
SOURCES = [
    {"title": "Rescheduling a course > Fees", "source": "rescheduling.md",
     "text": "Within 7 days of the start date: you can reschedule once for a $50 fee."},
    {"title": "Refunds and cancellations > How much you get back", "source": "refunds-and-cancellations.md",
     "text": "Cancel less than 7 days before the start date: no refund. Instead, you can move to a later date "
             "once, free of charge."},
]
ANSWERS = {
    "grounded": "Moving the course within 7 days of the start costs $50, once [1]. Cancelling now gives no refund, "
                "but you can move to a later date once, free [2].",
    "invented citation": "Moving the course costs $50 [1]. Cancelling gives no refund [4].",
    "number without a source": "Moving the course costs $50 [1]. Your refund would arrive in 5 to 10 business days.",
    "number not in its source": "Moving the course costs $75 [1]. Cancelling now gives no refund [2].",
}

for name, text in ANSWERS.items():
    report = check(text, SOURCES, QUESTION)
    problems = {k: v for k, v in report.items() if v and k not in ("ok", "cited")}
    print(f"{name.upper()}: {'OK' if report['ok'] else problems}")
print("\nRendered for the learner (grounded answer):\n")
print(render(ANSWERS["grounded"], SOURCES, check(ANSWERS["grounded"], SOURCES, QUESTION)))
