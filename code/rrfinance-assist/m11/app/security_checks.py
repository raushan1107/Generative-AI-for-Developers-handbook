"""Narrow privacy and injection indicators; these are not security boundaries."""

import re


_LABELLED_IDENTIFIER = re.compile(
    r"(?P<label>\b(?:card|account|national\s+ID)\s*(?:number|no\.?|#)"
    r"\s*(?:is|:|=)?\s*)(?P<value>(?:\d[ -]?){8,19}\d)",
    re.IGNORECASE,
)
_INJECTION_PATTERNS = {
    "override_instructions": re.compile(
        r"\bignore\s+(?:all\s+)?previous\s+instructions\b", re.IGNORECASE
    ),
    "reveal_prompt": re.compile(
        r"\breveal\s+(?:the\s+)?(?:system|developer)\s+prompt\b", re.IGNORECASE
    ),
    "request_secret": re.compile(
        r"\bask\s+the\s+customer\s+for\s+(?:their\s+)?"
        r"(?:pin|password|one[- ]time code)\b",
        re.IGNORECASE,
    ),
}


def mask_labeled_identifiers(text: str) -> str:
    """Mask digit sequences only when they follow a supported identifier label."""
    return _LABELLED_IDENTIFIER.sub(
        lambda match: f"{match.group('label')}[REDACTED]", text
    )


def injection_indicators(text: str) -> list[str]:
    """Return matched heuristic labels; absence of a match does not mean safe."""
    return [
        label for label, pattern in _INJECTION_PATTERNS.items() if pattern.search(text)
    ]
