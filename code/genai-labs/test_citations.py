"""Drill 06.10: citation checks, offline.  Run:  pytest -q test_citations.py"""
from citations import check, render, sentences

SOURCES = [
    {"title": "Fees and charges > Overdrafts", "source": "fees-and-charges.md",
     "text": "If a payment takes your balance below zero, we charge an overdraft fee of $29, at most 3 times per day."},
    {"title": "Lost or stolen cards > Report it and get a replacement", "source": "lost-stolen-cards.md",
     "text": "Express delivery within 2 business days costs $15."},
]


def test_a_well_cited_answer_passes():
    question = "I was overdrawn by $80, what's the fee?"
    report = check("Being $80 overdrawn costs a $29 fee [1]. Express card delivery costs $15 [2].", SOURCES, question)
    assert report["ok"] and report["cited"] == [1, 2]
    assert check("Being $80 overdrawn costs a $29 fee [1].", SOURCES)["unsupported"]   # 80 is in no source


def test_invented_citation_numbers_are_caught():
    report = check("The overdraft fee is $29 [1][7].", SOURCES)
    assert report["unknown"] == [7] and not report["ok"]


def test_numbers_without_a_citation_are_caught():
    report = check("The overdraft fee is $29. A new card arrives in 5 days [1].", SOURCES)
    assert report["uncited"] == ["The overdraft fee is $29."]
    assert report["unsupported"] == [{"sentence": "A new card arrives in 5 days [1].", "numbers": ["5"]}]


def test_a_number_missing_from_the_cited_source_is_caught():
    report = check("Express delivery costs $25 [2].", SOURCES)
    assert report["unsupported"] == [{"sentence": "Express delivery costs $25 [2].", "numbers": ["25"]}]


def test_citation_after_the_full_stop_belongs_to_that_sentence():
    assert sentences("The fee is $29. [1] Thanks!") == ["The fee is $29. [1]", "Thanks!"]
    assert check("The fee is $29. [1] Thanks!", SOURCES)["ok"]


def test_codes_are_not_treated_as_amounts():
    assert check("For RR-10477, see the overdraft rules [1].", SOURCES)["ok"]


def test_render_drops_invented_citations_and_lists_real_sources():
    answer = "The overdraft fee is $29 [1][7]."
    text = render(answer, SOURCES, check(answer, SOURCES))
    assert text == ("The overdraft fee is $29 [1].\n\nSources:\n"
                    "[1] Fees and charges > Overdrafts (fees-and-charges.md)")
