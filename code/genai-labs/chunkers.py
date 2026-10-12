"""Drill 05.7: three ways to cut documents into chunks before embedding them."""
import re
from pathlib import Path

HELP_DIR = Path(__file__).parent / "data" / "help"


def load_articles():
    """{"refunds-and-cancellations": "# Refunds and cancellations\n...", ...}"""
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(HELP_DIR.glob("*.md"))}


def fixed_size(text, size=300, overlap=50):
    """Windows of about `size` characters, cut at word boundaries, overlapping by about `overlap`."""
    words, chunks, start = text.split(), [], 0
    while start < len(words):
        end, length = start, 0
        while end < len(words) and length + len(words[end]) + 1 <= size:
            length += len(words[end]) + 1
            end += 1
        end = max(end, start + 1)
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        back, kept = end, 0                       # step back far enough to repeat ~overlap characters
        while back > start + 1 and kept < overlap:
            back -= 1
            kept += len(words[back]) + 1
        start = back
    return chunks


def by_sentences(text, max_chars=400):
    """Whole sentences, packed together until the next one would pass max_chars."""
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    chunks, current = [], ""
    for s in (s.strip() for s in sentences):
        if not s:
            continue
        if current and len(current) + len(s) + 1 > max_chars:
            chunks.append(current)
            current = s
        else:
            current = f"{current} {s}".strip()
    if current:
        chunks.append(current)
    return chunks


def by_headings(markdown):
    """One chunk per '## ' section, each starting with 'Article title > Section title'
    so the chunk still makes sense on its own."""
    title = re.search(r"^# (.+)$", markdown, re.M)
    title = title.group(1).strip() if title else ""
    parts = re.split(r"^## ", markdown, flags=re.M)
    intro = re.sub(r"^# .+$", "", parts[0], flags=re.M).strip()
    chunks = [f"{title}\n{intro}"] if intro else []
    for part in parts[1:]:
        heading, _, body = part.partition("\n")
        chunks.append(f"{title} > {heading.strip()}\n{body.strip()}")
    return chunks


STRATEGIES = {
    "fixed 300 chars": lambda t: fixed_size(t, 300, 50),
    "fixed 800 chars": lambda t: fixed_size(t, 800, 100),
    "sentences 400": lambda t: by_sentences(t, 400),
    "by headings": by_headings,
}
