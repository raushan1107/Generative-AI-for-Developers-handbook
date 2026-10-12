"""Tests for similarity.py. Run:  pytest -q test_similarity.py"""
import numpy as np
import pytest

from similarity import cosine, cosine_matrix, dot, euclidean


def test_cosine_ignores_length():
    assert cosine([1, 2], [2, 4]) == pytest.approx(1.0)
    assert cosine([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine([1, 0], [-1, 0]) == pytest.approx(-1.0)


def test_dot_and_euclidean():
    assert dot([1, 2], [3, 4]) == 11
    assert euclidean([0, 0], [3, 4]) == pytest.approx(5.0)


def test_on_unit_vectors_dot_equals_cosine():
    a, b = np.array([0.6, 0.8]), np.array([0.8, 0.6])
    assert dot(a, b) == pytest.approx(cosine(a, b))


def test_matrix_is_symmetric_with_ones_on_the_diagonal():
    m = cosine_matrix([[1, 0], [1, 1], [0, 3]])
    assert np.allclose(np.diag(m), 1.0) and np.allclose(m, m.T)
    assert m[0, 2] == pytest.approx(0.0)
