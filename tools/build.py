"""Build the Generative AI for Developers handbook.

Reads page fragments from src/**/*.html, wraps each one in the shared shell
(head, sidebar, top bar, hero, pager, footer) and writes the finished page to the
same relative path at the repository root. Code shown in the handbook is pulled
from the real, tested files under code/ so pages and code never drift apart.

Run from the repository root:   python tools/build.py
"""
import html
import json
import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
NAV = json.loads((ROOT / "tools" / "nav.json").read_text(encoding="utf-8"))

AUTHOR_URL = "https://raushan-ranjan.azurewebsites.net/"
FONTS = ("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700"
         "&family=JetBrains+Mono:wght@400;500;600&display=swap")

KIND_LABEL = {
    "home": "Home", "guide": "Guide", "setup": "Lab setup", "overview": "Overview", "topic": "Learn · Do · Check",
    "build": "Build", "recap": "Recap", "project": "Project", "labs": "Practice", "capstone": "Capstone",
    "osslab": "Open-source lab",
}
KIND_ICON = {
    "overview": "◎", "topic": "•", "build": "⚒", "recap": "✓", "setup": "›", "home": "⌂",
    "guide": "?", "project": "⚒", "labs": "▤", "capstone": "★", "osslab": "▸",
}
STEP_LABEL = {"run": "Run", "ask": "Ask AI", "write": "Your prompt", "verify": "Verify",
              "nocode": "No-code", "think": "Think", "portal": "Portal"}


# ---------------------------------------------------------------- navigation model
def flatten():
    """Ordered list of available pages with their context (section, module)."""
    pages = []
    for section in NAV["sections"]:
        for item in section.get("items", []):          # a section with "draft": true is built but not linked
            pages.append({**item, "section": section["title"], "module": None, "draft": bool(section.get("draft"))})
        for module in section.get("modules", []):
            if module.get("soon"):
                continue
            draft = bool(module.get("draft"))
            topics = [p for p in module["pages"] if p["kind"] == "topic"]
            for page in module["pages"]:
                ctx = {**page, "section": section["title"], "module": module, "part": section.get("part"),
                       "draft": draft}
                if page["kind"] == "topic":
                    ctx["topic_index"] = topics.index(page) + 1
                    ctx["topic_count"] = len(topics)
                pages.append(ctx)
    return pages


PAGES = flatten()
BY_ID = {p["id"]: p for p in PAGES}
# Draft modules ("draft": true in nav.json) are built but not linked from live pages:
# they stay "soon" in the live sidebar, out of the live pager, drill catalogue and cards.
# Draft pages link to each other so they can be reviewed. Remove the flag to go live.
LIVE = [p for p in PAGES if not p.get("draft")]
DRAFT = [p for p in PAGES if p.get("draft")]


def rel(from_path, to_path):
    depth = from_path.count("/")
    return "../" * depth + to_path


# ---------------------------------------------------------------- code inlining
def highlight_hash_comments(code):
    """HTML-escape code and wrap '#' comments (outside strings) in <span class="c">."""
    out, i, n = [], 0, len(code)
    buf = []
    state = None  # None, "'", '"', "'''", '"""'

    def flush():
        if buf:
            out.append(html.escape("".join(buf), quote=False))
            buf.clear()

    while i < n:
        ch = code[i]
        if state is None:
            if code.startswith('"""', i) or code.startswith("'''", i):
                state = code[i:i + 3]
                buf.append(state)
                i += 3
                continue
            if ch in "'\"":
                state = ch
                buf.append(ch)
                i += 1
                continue
            if ch == "#":
                end = code.find("\n", i)
                end = n if end == -1 else end
                flush()
                out.append('<span class="c">' + html.escape(code[i:end], quote=False) + "</span>")
                i = end
                continue
            buf.append(ch)
            i += 1
        else:
            if len(state) == 3:
                if code.startswith(state, i):
                    buf.append(state)
                    i += 3
                    state = None
                    continue
            else:
                if ch == "\\" and i + 1 < n:
                    buf.append(code[i:i + 2])
                    i += 2
                    continue
                if ch == state or ch == "\n":
                    state = None
            buf.append(ch)
            i += 1
    flush()
    return "".join(out)


def render_code(path_str, lines=None):
    path = ROOT / path_str
    if not path.exists():
        sys.exit(f"Missing code file referenced by a page: {path_str}")
    code = path.read_text(encoding="utf-8").rstrip("\n")
    if lines:
        a, b = (int(x) for x in lines.split("-"))
        code = "\n".join(code.splitlines()[a - 1:b])
    if path.suffix in {".py", ".txt", ".env", ".example", ".sh", ".ps1", ".toml", ".cfg"} or path.name.startswith(".env"):
        return highlight_hash_comments(code)
    return html.escape(code, quote=False)


CODE_RE = re.compile(r'<pre class="(?P<cls>[^"]*)"(?P<attrs>[^>]*?)\sdata-src="(?P<src>[^"]+)"(?P<rest>[^>]*)></pre>')


def inline_code(content):
    def repl(m):
        attrs = m.group("attrs") + m.group("rest")
        lines = re.search(r'data-lines="([^"]+)"', attrs)
        body = render_code(m.group("src"), lines.group(1) if lines else None)
        attrs = re.sub(r'\sdata-lines="[^"]+"', "", attrs)
        return f'<pre class="{m.group("cls")}"{attrs}><code>{body}</code></pre>'
    return CODE_RE.sub(repl, content)


# ---------------------------------------------------------------- drills index
DRILL_RE = re.compile(r'<div class="drill(?P<ex> exercise)?" id="(?P<id>[^"]+)" data-title="(?P<title>[^"]+)"'
                      r' data-time="(?P<time>[^"]+)" data-steps="(?P<steps>[^"]+)">')


def collect_drills(fragments):
    drills = []
    for page_id, content in fragments.items():
        for m in DRILL_RE.finditer(content):
            drills.append({"page": page_id, "id": m.group("id"), "title": html.unescape(m.group("title")),
                           "time": m.group("time"), "steps": m.group("steps").split(","),
                           "exercise": bool(m.group("ex"))})
    order = {p["id"]: i for i, p in enumerate(PAGES)}
    drills.sort(key=lambda d: (order.get(d["page"], 999), d["id"]))
    return drills


def drill_label(drill_id, short=False):
    """d01-5 -> 'Drill 01.5' (or '01.5'); b01-1 -> 'Milestone 1' (or 'M1')."""
    if drill_id.startswith("b"):
        n = int(drill_id[1:3])
        return f"M{n}" if short else f"Milestone {n}"
    core = drill_id[1:].replace("-", ".")
    return core if short else f"Drill {core}"


def step_badges(steps):
    return "".join(f'<span class="badge b-{s}">{STEP_LABEL[s]}</span>' for s in steps)


def drill_index_html(drills, here):
    rows, current = [], None
    for d in drills:
        if BY_ID[d["page"]].get("draft"):
            continue
        page = BY_ID[d["page"]]
        module = page.get("module")
        group = f'Module {module["num"]} · {module["title"]}' if module else page["section"]
        if group != current:
            rows.append(f'<tr class="group"><td colspan="4">{html.escape(group)}</td></tr>')
            current = group
        label = drill_label(d["id"])
        ex = ' <span class="badge b-exercise">Exercise</span>' if d["exercise"] else ""
        href = rel(here, page["path"]) + "#" + d["id"]
        rows.append(
            f'<tr data-steps="{",".join(d["steps"])}"><td class="mono">{label}</td>'
            f'<td><a href="{href}">{html.escape(d["title"])}</a>{ex}<div class="small muted">{html.escape(page["title"])}</div></td>'
            f'<td>{step_badges(d["steps"])}</td><td class="mono">{d["time"]}</td></tr>')
    return ('<div class="table-wrap"><table class="drill-table"><thead><tr><th>Drill</th><th>What you do</th>'
            '<th>Step types</th><th>Time</th></tr></thead><tbody>' + "\n".join(rows) + "</tbody></table></div>")


def module_pages_html(num, drills, here):
    module = next(m for s in NAV["sections"] for m in s.get("modules", []) if m["num"] == num)
    cards = []
    for page in module["pages"]:
        if page["kind"] == "overview":
            continue
        page_drills = [d for d in drills if d["page"] == page["id"]]
        drill_list = "".join(
            f'<li><span class="mono">{drill_label(d["id"], short=True)}</span> {html.escape(d["title"])} '
            f'<span class="muted">· {d["time"]}</span></li>' for d in page_drills)
        kind = page["kind"]
        tag = {"topic": "Learn · Do · Check", "build": "Traincrest Assist", "recap": "Check"}.get(kind, kind)
        cards.append(
            f'<a class="page-card k-{kind}" href="{rel(here, page["path"])}"><span class="pc-tag">{tag}</span>'
            f'<b>{html.escape(page["title"])}</b>' + (f'<ul>{drill_list}</ul>' if drill_list else "") + "</a>")
    return '<div class="page-cards">' + "\n".join(cards) + "</div>"


# ---------------------------------------------------------------- shell pieces
def sidebar_html(page):
    here = page["path"]
    parts = [
        f'<a class="sb-brand" href="{rel(here, "index.html")}">'
        '<span class="sb-mark">AI</span><span class="sb-brand-text"><b>Generative AI for Developers</b>'
        '<small>Raushan Ranjan · RR Skillverse</small></span></a>',
        '<div class="sb-search"><input type="search" placeholder="Filter pages…" aria-label="Filter pages" data-nav-filter></div>',
        '<nav class="sb-nav" aria-label="Handbook pages">',
    ]
    for section in NAV["sections"]:
        if section.get("draft") and not page.get("draft"):          # draft sections are invisible on live pages
            continue
        parts.append(f'<div class="sb-section"><div class="sb-title">{html.escape(section["title"])}</div>')
        for item in section.get("items", []):
            cls = "active" if item["id"] == page["id"] else ""
            parts.append(f'<a class="sb-link {cls}" data-page-id="{item["id"]}" href="{rel(here, item["path"])}">'
                         f'<span class="sb-ico">{KIND_ICON.get(item["kind"], "•")}</span>{html.escape(item["title"])}</a>')
        for module in section.get("modules", []):
            if module.get("soon") or (module.get("draft") and not page.get("draft")):
                parts.append(f'<div class="sb-module soon"><span class="sb-num">{module["num"]}</span>'
                             f'{html.escape(module["title"])}<span class="sb-soon">soon</span></div>')
                continue
            is_open = any(p["id"] == page["id"] for p in module["pages"])
            parts.append(f'<details class="sb-mod"{" open" if is_open else ""}><summary><span class="sb-num">{module["num"]}</span>'
                         f'{html.escape(module["title"])}</summary>')
            for p in module["pages"]:
                cls = "active" if p["id"] == page["id"] else ""
                parts.append(f'<a class="sb-link sub k-{p["kind"]} {cls}" data-page-id="{p["id"]}" href="{rel(here, p["path"])}">'
                             f'<span class="sb-ico">{KIND_ICON.get(p["kind"], "•")}</span>{html.escape(p["title"])}</a>')
            parts.append("</details>")
        parts.append("</div>")
    parts.append("</nav>")
    parts.append(f'<div class="sb-foot">Written by <a href="{AUTHOR_URL}" target="_blank" rel="noopener noreferrer">'
                 'Raushan Ranjan</a> (MCT)<br><span>RR Skillverse · © 2026</span></div>')
    return "\n".join(parts)


def crumbs_html(page):
    here = page["path"]
    bits = [f'<a href="{rel(here, "index.html")}">Handbook</a>']
    if page.get("module"):
        m = page["module"]
        overview = next(p for p in m["pages"] if p["kind"] == "overview")
        bits.append(f'<span>Part {page["part"]}</span>')
        bits.append(f'<a href="{rel(here, overview["path"])}">Module {m["num"]}</a>')
        if page["kind"] != "overview":
            bits.append(f'<span>{html.escape(page["title"])}</span>')
    elif page["id"] != "home":
        bits.append(f'<span>{html.escape(page["section"])}</span>')
        bits.append(f'<span>{html.escape(page["title"])}</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<i>/</i>'.join(bits) + "</nav>"


def eyebrow(page):
    m = page.get("module")
    k = page["kind"]
    if m:
        if k == "topic":
            return f'Module {m["num"]} · Topic {page["topic_index"]} of {page["topic_count"]}'
        return f'Module {m["num"]} · ' + {"overview": "Overview", "build": "Build milestone", "recap": "Recap"}[k]
    if k == "setup":
        setup = [p for p in PAGES if p["kind"] == "setup"]
        return f"Lab setup · Step {setup.index(page) + 1} of {len(setup)}"
    return KIND_LABEL.get(k, "")


def hero_html(page, meta):
    chips = "".join(f'<span class="chip">{html.escape(c)}</span>' for c in meta.get("chips", []))
    flow = ""
    if page["kind"] == "topic":
        flow = ('<div class="flow"><a href="#learn"><b>1</b>Learn</a><span>→</span><a href="#do"><b>2</b>Do</a>'
                '<span>→</span><a href="#check"><b>3</b>Check</a>'
                + (f'<em>{html.escape(meta["time"])}</em>' if meta.get("time") else "") + "</div>")
    elif meta.get("time"):
        flow = f'<div class="flow"><em>{html.escape(meta["time"])}</em></div>'
    lead = f'<p class="lead">{meta["lead"]}</p>' if meta.get("lead") else ""
    return (f'<header class="page-hero"><span class="eyebrow">{eyebrow(page)}</span>'
            f'<h1>{meta.get("h1", page["title"])}</h1>{lead}'
            + (f'<div class="chips">{chips}</div>' if chips else "") + flow + "</header>")


def pager_html(page):
    seq = DRAFT if page.get("draft") else LIVE
    i = seq.index(page)
    here = page["path"]

    def label(p):
        m = p.get("module")
        return (f'{m["num"]} · ' if m else "") + html.escape(p["title"])

    prev_ = seq[i - 1] if i > 0 else None
    next_ = seq[i + 1] if i + 1 < len(seq) else None
    a = (f'<a class="prev" href="{rel(here, prev_["path"])}"><small>Previous</small><span>← {label(prev_)}</span></a>'
         if prev_ else "<span></span>")
    b = (f'<a class="next" href="{rel(here, next_["path"])}"><small>Next</small><span>{label(next_)} →</span></a>'
         if next_ else "<span></span>")
    done = ""
    if page["kind"] in {"topic", "build", "setup", "recap"}:
        done = (f'<label class="page-done"><input type="checkbox" data-page-done="{page["id"]}"> '
                'Mark this page as done</label>')
    return f'{done}<nav class="pager" aria-label="Page navigation">{a}{b}</nav>'


SVG_DEFS = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>'
            '<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" class="s-head"/></marker>'
            '<marker id="ah-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" class="s-head-accent"/></marker></defs></svg>')

THEME_BOOT = ("<script>try{var t=localStorage.getItem('genai-theme');if(t==='light'||t==='dark')"
              "document.documentElement.setAttribute('data-theme',t);}catch(e){}</script>")


def page_html(page, meta, content):
    here = page["path"]
    title = meta.get("short", page["title"])
    if page["id"] == "home":
        title = "Generative AI for Developers | by Raushan Ranjan, MCT"
    hero = "" if meta.get("layout") == "home" else hero_html(page, meta)
    kind = KIND_LABEL.get(page["kind"], "") + (" · Draft" if page.get("draft") else "")
    robots = '<meta name="robots" content="noindex">\n' if page.get("draft") else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(meta.get('description', ''), quote=True)}">
<meta name="author" content="Raushan Ranjan (MCT)">
{robots}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="{rel(here, 'assets/css/handbook.css')}">
{THEME_BOOT}
<script src="{rel(here, 'assets/js/handbook.js')}" defer></script>
</head>
<body class="kind-{page['kind']}" data-page="{page['id']}">
{SVG_DEFS}
<div class="app">
<aside class="sidebar" id="sidebar">
{sidebar_html(page)}
</aside>
<div class="sb-scrim" data-nav-close></div>
<div class="main">
<header class="topbar">
  <button class="icon-btn menu-btn" type="button" data-nav-open aria-label="Open navigation">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
  </button>
  {crumbs_html(page)}
  <span class="kind-pill">{kind}</span>
  <button class="icon-btn" type="button" data-theme-toggle aria-label="Toggle light or dark theme">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
  </button>
  <div class="progress" aria-hidden="true"></div>
</header>
<div class="page-wrap">
<main class="page" id="main">
{hero}
<div class="content">
{content}
</div>
{pager_html(page)}
</main>
<aside class="otp" aria-label="On this page"></aside>
</div>
<footer class="site-footer">
  <span>Generative AI for Developers · Written by <a class="author-link" href="{AUTHOR_URL}" target="_blank" rel="noopener noreferrer">Raushan Ranjan</a> (MCT) · RR Skillverse · © 2026</span>
  <span>Not affiliated with Microsoft, OpenAI, Anthropic or GitHub. TrainCrest scenario data and policies in this handbook are fictional. Model names, limits and prices change often; confirm them in the official documentation.</span>
</footer>
</div>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------- main
META_RE = re.compile(r"\A\s*<!--meta\s*(\{.*?\})\s*-->", re.S)


def main():
    fragments, metas = {}, {}
    for src in sorted(SRC.rglob("*.html")):
        text = src.read_text(encoding="utf-8")
        m = META_RE.match(text)
        if not m:
            sys.exit(f"{src}: missing <!--meta {{...}} --> header")
        meta = json.loads(m.group(1))
        page_id = meta["id"]
        if page_id not in BY_ID:
            sys.exit(f"{src}: id {page_id!r} is not in tools/nav.json")
        expected = SRC / BY_ID[page_id]["path"]
        if src.resolve() != expected.resolve():
            sys.exit(f"{src}: should live at {expected} to match nav.json")
        fragments[page_id] = text[m.end():]
        metas[page_id] = meta

    missing = [p["path"] for p in PAGES if p["id"] not in fragments]
    if missing:
        print("Warning: pages in nav.json without a source file:", ", ".join(missing))

    drills = collect_drills(fragments)
    draft_paths = {p["path"] for p in DRAFT}
    for page_id, content in fragments.items():
        page = BY_ID[page_id]
        content = inline_code(content)
        content = content.replace("<!--DRILL_INDEX-->", drill_index_html(drills, page["path"]))
        content = re.sub(r"<!--MODULE_PAGES:(\d\d)-->",
                         lambda mm: module_pages_html(mm.group(1), drills, page["path"]), content)
        if not page.get("draft"):
            base = posixpath.dirname(page["path"])
            for href in re.findall(r'href="([^"#:]+)', content):
                if posixpath.normpath(posixpath.join(base, href)) in draft_paths:
                    sys.exit(f"{page['path']}: links to draft page {href}; publish the module first")
        out = ROOT / page["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page_html(page, metas[page_id], content), encoding="utf-8", newline="\n")
    live = [d for d in drills if not BY_ID[d["page"]].get("draft")]
    drafts = sorted({p["module"]["num"] for p in DRAFT if p.get("module")})
    draft_sections = sorted({p["section"] for p in DRAFT if not p.get("module")})
    print(f"Built {len(fragments)} pages, {len(live)} drills indexed"
          + (f" ({len(drills) - len(live)} more in draft modules {', '.join(drafts)}, not linked)." if drafts else ".")
          + (f" Draft sections: {', '.join(draft_sections)}." if draft_sections else ""))


if __name__ == "__main__":
    main()
