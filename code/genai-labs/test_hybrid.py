"""Tests for hybrid.py (offline). Run:  pytest -q test_hybrid.py"""
import numpy as np

from hybrid import bm25_ranking, rrf, tokenize, vector_ranking

DOCS = ["AZ-104 Azure Administrator exam prep", "Python for beginners", "Azure fundamentals AZ-900",
        "Kubernetes for developers"]


def test_tokenize_keeps_codes_and_drops_filler():
    assert tokenize("Prep for AZ-104!") == ["prep", "az-104"]
    assert tokenize("Is there a discount for teams?") == ["discount", "team"]


def test_bm25_finds_exact_codes():
    assert bm25_ranking("AZ-104", DOCS) == [0]


def test_vector_ranking_orders_by_cosine():
    vectors = np.array([[1, 0], [0, 1], [0.7, 0.7]])
    assert vector_ranking(np.array([1, 0.1]), vectors) == [0, 2, 1]


def test_rrf_rewards_agreement():
    keyword, vector = [0, 2, 1], [2, 3, 0]
    fused = rrf([keyword, vector])
    assert fused[:2] == [2, 0]               # 2 and 0 are high in both lists
    assert set(fused) == {0, 1, 2, 3}        # a document in only one list still counts
