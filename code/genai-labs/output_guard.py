"""Drill 03.13 (reference solution): check model output before showing or publishing it."""
import re

URL = re.compile(r"(?:https?://|www\.)\S+|\b(?:[a-z0-9-]+\.)+(?:com|net|org|io|co|xyz|info|example)\b", re.I)
EMAIL = re.compile(r"\b[\w.+-]+@(?:[\w-]+\.)+[\w-]+\b")
PHONE = re.compile(r"(?<!\w)\+?\d(?:[\s-]?\d){8,}(?!\w)")
INJECTION_ECHO = re.compile(r"ignore (?:all |your )?(?:previous |prior )?instructions", re.I)


def _host(url_text):
    host = re.sub(r"^(?:https?://)?(?:www\.)?", "", url_text.lower())
    return re.split(r"[/?#:]", host, maxsplit=1)[0].rstrip(".,;)")


def check_output(text, allowed_domains=("traincrest.example",)):
    """Return a sorted list of problem names found in `text`; an empty list means it passed.

    URLs are allowed only if their host is one of `allowed_domains` or a subdomain of one.
    """
    problems = set()
    text_without_emails = EMAIL.sub(" ", text)
    if EMAIL.search(text):
        problems.add("email")
    for match in URL.finditer(text_without_emails):
        host = _host(match.group(0))
        if not any(host == d or host.endswith("." + d) for d in allowed_domains):
            problems.add("url")
    if PHONE.search(text):
        problems.add("phone")
    if INJECTION_ECHO.search(text):
        problems.add("injection_echo")
    return sorted(problems)
