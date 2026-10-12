"""Module 06 helper: chunking for answers, not just for search.
Milestone 5 cut articles at '## ' headings but dropped the text before the first heading.
Here the intro is kept as an 'Overview' chunk, long sections are split at paragraph breaks
(each piece keeps its 'Title > Section' header), and every chunk carries what citations need."""
import re

from ingest import Doc

CHUNKER_VERSION = "sections-v2"


def sections(doc: Doc):
    """Yield (heading, body) for the intro and each '## ' section."""
    text = re.sub(r"^# .+\n?", "", doc.text, count=1)          # the title goes into every header instead
    intro, *parts = re.split(r"^## ", text, flags=re.M)
    if intro.strip():
        yield "Overview", intro.strip()
    for part in parts:
        heading, _, body = part.partition("\n")
        if body.strip():
            yield heading.strip(), body.strip()


def split_long(body: str, max_chars: int):
    """Split at blank lines (then single lines) so no piece is longer than max_chars, where possible."""
    pieces, current = [], ""
    for para in re.split(r"\n\s*\n|\n(?=- )", body):
        para = para.strip()
        sep = "\n" if para.startswith("- ") else "\n\n"           # keep list items together visually
        if current and len(current) + len(para) + len(sep) > max_chars:
            pieces.append(current)
            current = para
        else:
            current = f"{current}{sep}{para}" if current else para
    return pieces + ([current] if current else [])


def chunk(doc: Doc, max_chars: int = 900):
    """Chunks as dicts: id like 'refunds-and-cancellations#2', the header, text, source and audience."""
    chunks = []
    for heading, body in sections(doc):
        for piece in split_long(body, max_chars):
            n = len(chunks) + 1
            chunks.append({"id": f"{doc.id}#{n}", "doc_id": doc.id, "title": f"{doc.title} > {heading}",
                           "text": f"{doc.title} > {heading}\n{piece}", "source": doc.source,
                           "audience": doc.audience})
    return chunks


def chunk_all(docs, max_chars: int = 900):
    return [c for d in docs for c in chunk(d, max_chars)]
