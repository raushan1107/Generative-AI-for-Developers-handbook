"""Deterministic classification metrics and explicit release thresholds."""

import math
from collections.abc import Mapping, Sequence


def classification_metrics(
    expected: Sequence[str], predicted: Sequence[str], positive_label: str
) -> dict[str, float]:
    if not expected or len(expected) != len(predicted):
        raise ValueError("Expected and predicted labels must be non-empty and aligned")
    if not positive_label:
        raise ValueError("A positive label is required")

    true_positive = sum(
        actual == positive_label and guess == positive_label
        for actual, guess in zip(expected, predicted)
    )
    false_positive = sum(
        actual != positive_label and guess == positive_label
        for actual, guess in zip(expected, predicted)
    )
    false_negative = sum(
        actual == positive_label and guess != positive_label
        for actual, guess in zip(expected, predicted)
    )
    correct = sum(actual == guess for actual, guess in zip(expected, predicted))
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative

    return {
        "accuracy": correct / len(expected),
        "precision": (
            true_positive / precision_denominator if precision_denominator else 0.0
        ),
        "recall": true_positive / recall_denominator if recall_denominator else 0.0,
    }


def release_gate(
    metrics: Mapping[str, float], minimums: Mapping[str, float]
) -> list[str]:
    """Return failed metric names; callers decide whether to block a release."""
    failures: list[str] = []
    for name, minimum in minimums.items():
        value = metrics.get(name)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not isinstance(minimum, (int, float))
            or isinstance(minimum, bool)
            or not math.isfinite(value)
            or not math.isfinite(minimum)
            or not 0.0 <= minimum <= 1.0
            or value < minimum
        ):
            failures.append(name)
    return failures
