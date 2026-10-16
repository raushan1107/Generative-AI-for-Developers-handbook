"""Tests for chunkers.py (offline). Run:  pytest -q test_chunkers.py"""
from chunkers import by_headings, by_sentences, fixed_size, load_articles

MD = "# Cards\n\nIntro line.\n\n## Freeze it first\nFreeze it in the app. It takes effect instantly.\n\n## Replacement\n5 to 7 business days.\n"


def test_fixed_size_respects_size_and_overlaps():
    text = " ".join(f"word{i}" for i in range(200))
    chunks = fixed_size(text, size=100, overlap=20)
    assert all(len(c) <= 100 for c in chunks)
    assert chunks[0].split()[-1] in chunks[1]                 # the end of one chunk starts the next
    assert chunks[-1].endswith("word199")


def test_sentences_are_never_cut():
    chunks = by_sentences("One. Two two. Three three three.", max_chars=15)
    assert chunks == ["One. Two two.", "Three three three."]


def test_headings_keep_their_context():
    chunks = by_headings(MD)
    assert chunks[0] == "Cards\nIntro line."
    assert chunks[1].startswith("Cards > Freeze it first\n") and "instantly" in chunks[1]
    assert len(chunks) == 3


def test_every_article_has_a_title_and_sections():
    for name, md in load_articles().items():
        assert md.startswith("# "), name
        assert len(by_headings(md)) >= 3, name
