"""Tiny edit helpers: every replacement must match exactly once (or `count` times)."""
from pathlib import Path


def sub(path, pairs, count=1):
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    for a, b in pairs:
        n = s.count(a)
        if n != count and not (count == 0 and n >= 1):
            raise SystemExit(f"{path}: expected {count} match(es), found {n}: {a[:80]!r}")
        s = s.replace(a, b)
    p.write_text(s, encoding="utf-8")


def finance_after(path, anchor_start, html):
    """Insert an 'In finance' callout right after the block that starts with anchor_start
    (the first </div> after it closes the callout)."""
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    if 'class="callout finance"' in s:
        raise SystemExit(f"{path}: already has a finance callout")
    i = s.index(anchor_start)
    j = s.index("</div>", i) + len("</div>")
    block = ('\n\n<div class="callout finance">\n  <div class="c-label">In finance</div>\n  '
             + html.strip() + "\n</div>")
    p.write_text(s[:j] + block + s[j:], encoding="utf-8")


def replace_between(path, start, end, new):
    """Replace the text from `start` (inclusive) up to `end` (exclusive)."""
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    i = s.index(start)
    j = s.index(end, i)
    p.write_text(s[:i] + new + s[j:], encoding="utf-8")
