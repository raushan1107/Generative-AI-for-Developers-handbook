"""Guardrails around untrusted text (milestone 3). Module 10 adds more layers."""
import re

URL = re.compile(r"(?:https?://|www\.)\S+|\b(?:[a-z0-9-]+\.)+(?:com|net|org|io|co|xyz|info|example)\b", re.I)
EMAIL = re.compile(r"\b[\w.+-]+@(?:[\w-]+\.)+[\w-]+\b")
PHONE = re.compile(r"(?<!\w)\+?\d(?:[\s-]?\d){8,}(?!\w)")
INJECTION_ECHO = re.compile(r"ignore (?:all |your )?(?:previous |prior )?instructions", re.I)
OUR_TAGS = re.compile(r"</?\s*(?:message|learner_message|policy|ticket)\s*>", re.I)

ALLOWED_DOMAINS = ("traincrest.example",)


def neutralise_tags(text: str) -> str:
    """Remove our own delimiter tags from untrusted text, so it can't 'close' a <message> block
    early and smuggle text in as if it were instructions."""
    return OUR_TAGS.sub("", text)


def _host(url_text: str) -> str:
    host = re.sub(r"^(?:https?://)?(?:www\.)?", "", url_text.lower())
    return re.split(r"[/?#:]", host, maxsplit=1)[0].rstrip(".,;)")


def check_output(text: str) -> list[str]:
    """Return problem names found in model output (empty list = passed)."""
    problems = set()
    if EMAIL.search(text):
        problems.add("email")
    for match in URL.finditer(EMAIL.sub(" ", text)):
        host = _host(match.group(0))
        if not any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS):
            problems.add("url")
    if PHONE.search(text):
        problems.add("phone")
    if INJECTION_ECHO.search(text):
        problems.add("injection_echo")
    return sorted(problems)
