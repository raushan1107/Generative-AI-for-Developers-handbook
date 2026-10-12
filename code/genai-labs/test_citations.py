"""Drill 06.10: citation checks, offline.  Run:  pytest -q test_citations.py"""
from citations import check, render, sentences

SOURCES = [
    {"title": "Refunds > How much you get back", "source": "refunds-and-cancellations.md",
     "text": "Cancel 7 to 13 days before the start date: 50% refund."},
    {"title": "Rescheduling > Fees", "source": "rescheduling.md",
     "text": "Within 7 days of the start date: you can reschedule once for a $50 fee."},
]


def test_a_well_cited_answer_passes():
    question = "What if I cancel 10 days before?"
    report = check("Cancelling 10 days before gives a 50% refund [1]. Moving the date costs $50 [2].", SOURCES, question)
    assert report["ok"] and report["cited"] == [1, 2]
    assert check("Cancelling 10 days before gives a 50% refund [1].", SOURCES)["unsupported"]   # 10 is in no source


def test_invented_citation_numbers_are_caught():
    report = check("You get a 50% refund [1][7].", SOURCES)
    assert report["unknown"] == [7] and not report["ok"]


def test_numbers_without_a_citation_are_caught():
    report = check("You get a 50% refund. It arrives in 5 days [1].", SOURCES)
    assert report["uncited"] == ["You get a 50% refund."]
    assert report["unsupported"] == [{"sentence": "It arrives in 5 days [1].", "numbers": ["5"]}]


def test_a_number_missing_from_the_cited_source_is_caught():
    report = check("Moving the date costs $75 [2].", SOURCES)
    assert report["unsupported"] == [{"sentence": "Moving the date costs $75 [2].", "numbers": ["75"]}]


def test_citation_after_the_full_stop_belongs_to_that_sentence():
    assert sentences("You get 50% back. [1] Thanks!") == ["You get 50% back. [1]", "Thanks!"]
    assert check("You get 50% back. [1] Thanks!", SOURCES)["ok"]


def test_codes_are_not_treated_as_amounts():
    assert check("For TC-10477, see the refund rules [1].", SOURCES)["ok"]


def test_render_drops_invented_citations_and_lists_real_sources():
    answer = "You get a 50% refund [1][7]."
    text = render(answer, SOURCES, check(answer, SOURCES))
    assert text == ("You get a 50% refund [1].\n\nSources:\n"
                    "[1] Refunds > How much you get back (refunds-and-cancellations.md)")
