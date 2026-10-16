"""Module 06 helper: document ingestion.
Load a folder of mixed documents (markdown, HTML, plain text, CSV FAQ) into one clean shape:
a title, markdown-style text with '## ' sections, the source file, who may see it, and a content
hash so a re-run can tell new, changed and unchanged documents apart."""
import csv
import hashlib
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

DATA = Path(__file__).parent / "data"


@dataclass
class Doc:
    id: str          # stable: the file name without extension
    title: str
    text: str        # clean text; sections start with "## "
    source: str      # file name, shown in citations
    audience: str    # "public" or "staff": who may see it (a retrieval filter later)
    hash: str = ""


def clean(text: str) -> str:
    """Normalise what copy-paste and exports leave behind: odd spaces, line endings, blank-line runs."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ").replace("​", "")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def content_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def load_markdown(path: Path) -> tuple[str, str]:
    text = clean(path.read_text(encoding="utf-8"))
    title = re.search(r"^# (.+)$", text, re.M)
    return (title.group(1).strip() if title else path.stem), text


def sentence_case(text: str) -> str:
    """'RULE FR-12 ALERTS' -> 'Rule FR-12 alerts': lower-case words, but keep codes with digits."""
    words = [w if any(ch.isdigit() for ch in w) else w.lower() for w in text.split()]
    out = " ".join(words)
    return out[:1].upper() + out[1:]


def load_text(path: Path) -> tuple[str, str]:
    """Plain text from an old system: first line is the title, UPPER-CASE lines are headings."""
    lines = clean(path.read_text(encoding="utf-8")).split("\n")
    title = sentence_case(lines[0])
    body = [f"## {sentence_case(line)}" if line.isupper() and len(line.split()) <= 8 else line
            for line in lines[1:]]
    return title, f"# {title}\n" + "\n".join(body)


class _MainText(HTMLParser):
    """Keep the page's content, drop the chrome: navigation, header, footer, sidebars, scripts, styles."""
    SKIP = {"nav", "header", "footer", "aside", "script", "style", "head"}
    PREFIX = {"h1": "# ", "h2": "## ", "h3": "### ", "li": "- "}

    def __init__(self):
        super().__init__()
        self.out, self.skipping = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skipping += 1
        elif not self.skipping and tag in self.PREFIX | {"p": ""}:
            self.out.append("\n\n" if tag != "li" else "\n")
            self.out.append(self.PREFIX.get(tag, ""))

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skipping:
            self.skipping -= 1

    def handle_data(self, data):
        if not self.skipping:
            self.out.append(re.sub(r"\s+", " ", data))


def load_html(path: Path) -> tuple[str, str]:
    parser = _MainText()
    parser.feed(path.read_text(encoding="utf-8"))          # entities like &rsaquo; are decoded for us
    text = clean("".join(parser.out))
    text = "\n".join(line.strip() for line in text.split("\n"))
    title = re.search(r"^# (.+)$", text, re.M)
    return (title.group(1).strip() if title else path.stem), clean(text)


def load_csv_faq(path: Path) -> tuple[str, str]:
    """A question,answer spreadsheet: each row becomes one '## question' section."""
    title = re.sub(r"\bfaq\b", "FAQ", sentence_case(path.stem.replace("-", " ")))
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    sections = [f"## {r['question'].strip()}\n{r['answer'].strip()}" for r in rows if r.get("answer")]
    return title, f"# {title}\n\n" + "\n\n".join(sections)


LOADERS = {".md": load_markdown, ".html": load_html, ".htm": load_html, ".txt": load_text, ".csv": load_csv_faq}


def load_folder(folder, audience: str):
    """Return (docs, report). The report has one line per file: loaded, or why it was skipped."""
    docs, report, seen = [], [], {}
    for path in sorted(Path(folder).iterdir()):
        loader = LOADERS.get(path.suffix.lower())
        if loader is None:
            report.append((path.name, "skipped: unsupported format"))
            continue
        title, text = loader(path)
        digest = content_hash(text)
        if len(text) < 40:
            report.append((path.name, "skipped: empty"))
        elif digest in seen:
            report.append((path.name, f"skipped: duplicate of {seen[digest]}"))
        else:
            seen[digest] = path.name
            docs.append(Doc(path.stem, title, text, path.name, audience, digest))
            report.append((path.name, f"loaded: {text.count(chr(10) + '## ')} sections, {len(text)} chars"))
    return docs, report


def load_knowledge_base():
    """RR Finance Bank's knowledge base: public help-centre articles plus internal staff documents."""
    public, _ = load_folder(DATA / "help", "public")
    staff, _ = load_folder(DATA / "internal", "staff")
    return public + staff
