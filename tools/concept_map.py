"""Generate concept-map pages from tools/maps/*.json into src/maps/*.html.

Each map is one Part (and, at the end, the whole course): a short story, a one-picture overview,
then an expandable tree Part > Module > Topic. Every topic has a definition, an example, an optional finance example, a use case,
the key point to keep in mind, and "connects to" links that open and highlight related topics.
Run before tools/build.py whenever a map's JSON changes:  python tools/concept_map.py"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPS = ROOT / "tools" / "maps"
TONES = ["s-blue", "s-teal", "s-violet", "s-amber", "s-rose"]


def esc(text):
    return html.escape(text, quote=True)


def rel(to_path, from_path):
    return "../" * from_path.count("/") + to_path


def overview_svg(data):
    """One picture of the Part: modules as columns, each topic a box, story labels on top."""
    modules = data["modules"]
    col_w, gap, top = 300, 20, 96
    rows = max(len(m["topics"]) for m in modules)
    height = top + rows * 34 + 40
    width = len(modules) * col_w + (len(modules) - 1) * gap + 40
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="cm-t cm-d">',
             f'<title id="cm-t">{esc(data["title"])}: all topics at once</title>',
             f'<desc id="cm-d">{esc(" ".join(f"{s[0]} ({s[1]}): {s[2]}" for s in data["story"]))}</desc>']
    for i, m in enumerate(modules):
        x = 20 + i * (col_w + gap)
        tone = TONES[i % len(TONES)]
        story = data["story"][i] if i < len(data["story"]) else [m["title"], f"Module {m['num']}", ""]
        parts.append(f'<rect x="{x}" y="14" width="{col_w}" height="{height - 28}" rx="14" class="{tone}"/>')
        parts.append(f'<text x="{x + 16}" y="40" class="t-m">MODULE {m["num"]} · {esc(story[0].upper())}</text>')
        parts.append(f'<text x="{x + 16}" y="64" class="t-b">{esc(m["title"])}</text>')
        for j, t in enumerate(m["topics"]):
            y = top + j * 34 - 16
            parts.append(f'<a href="#t-{t["id"]}" class="cm-svg-link"><rect x="{x + 14}" y="{y}" width="{col_w - 28}" height="28" '
                         f'rx="7" class="s-surface"/><text x="{x + 26}" y="{y + 19}" class="t-s">{esc(t["title"])}</text></a>')
        if i < len(modules) - 1:
            parts.append(f'<path d="M{x + col_w} {height / 2} H{x + col_w + gap - 2}" class="s-arrow-accent" marker-end="url(#ah-a)"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def topic_html(t, titles, page_path):
    links = "".join(
        f'<button type="button" class="cm-link" data-target="t-{cid}" title="{esc(why)}">'
        f'{esc(titles[cid])}<span>{esc(why)}</span></button>' for cid, why in t["connects"])
    return f'''<details class="cm-topic" id="t-{t["id"]}">
  <summary><b>{esc(t["title"])}</b><span class="cm-short">{esc(t["definition"])}</span></summary>
  <dl class="cm-facts">
    <dt>Definition</dt><dd>{esc(t["definition"])}</dd>
    <dt>Example</dt><dd>{esc(t["example"])}</dd>{f"""
    <dt>In finance</dt><dd>{esc(t["finance"])}</dd>""" if t.get("finance") else ""}
    <dt>Where it's used</dt><dd>{esc(t["usecase"])}</dd>
    <dt>Keep in mind</dt><dd>{esc(t["keep"])}</dd>
  </dl>
  <div class="cm-connects"><span class="cm-label">Connects to</span>{links}</div>
  <p class="cm-more"><a href="{rel(t["page"], page_path)}">Read the full topic page →</a></p>
</details>'''


def page_html(data):
    titles = {t["id"]: t["title"] for m in data["modules"] for t in m["topics"]}
    for m in data["modules"]:
        for t in m["topics"]:
            for cid, _ in t["connects"]:
                if cid not in titles:
                    sys.exit(f'{data["id"]}: topic {t["id"]} connects to unknown topic {cid!r}')
    meta = {"id": data["id"], "short": data["title"].title(), "h1": data["h1"], "description": data["description"],
            "lead": data["lead"], "chips": data["chips"]}
    story = "".join(f'<div class="card"><span class="num">{esc(s[1].upper())}</span><h3>{esc(s[0])}</h3><p>{esc(s[2])}</p></div>'
                    for s in data["story"])
    modules = []
    for m in data["modules"]:
        topics = "\n".join(topic_html(t, titles, data["path"]) for t in m["topics"])
        modules.append(f'''<details class="cm-module" id="m-{m["num"]}">
  <summary><span class="cm-num">{m["num"]}</span><b>{esc(m["title"])}</b><span class="cm-short">{esc(m["tagline"])} · {len(m["topics"])} topics</span></summary>
  <div class="cm-topics">
{topics}
  <p class="cm-more"><a href="{rel(m["overview"], data["path"])}">Module {m["num"]} overview →</a></p>
  </div>
</details>''')
    count = sum(len(m["topics"]) for m in data["modules"])
    return f'''<!--meta
{json.dumps(meta, ensure_ascii=False)}
-->
<h2 id="story">The story in one line</h2>
<div class="cards">{story}</div>

<h2 id="picture">Everything at once</h2>
<p>Every topic of this Part on one picture. Read the columns left to right; click a topic to jump to its card below.</p>
<figure class="diagram">
  <div class="frame">
{overview_svg(data)}
  </div>
  <figcaption><b>{len(data["modules"])} modules, {count} topics, one story.</b> Each column builds on the one before it.</figcaption>
</figure>

<h2 id="tree">Explore the map</h2>
<p>Open a module, then a topic. Each topic shows a definition, an example, an example from finance, where it's used, the point to keep in mind, and the topics it <em>connects to</em>; click a connection to jump there.</p>
<div class="cm-tools">
  <button type="button" class="btn" data-cm="expand">Expand all</button>
  <button type="button" class="btn" data-cm="collapse">Collapse all</button>
  <input type="search" placeholder="Find a term, e.g. tokens" aria-label="Find a term" data-cm="filter">
</div>
<div class="cmap" data-cmap>
<details class="cm-root" open>
  <summary><b>{esc(data["title"])}</b><span class="cm-short">{len(data["modules"])} modules · {count} topics</span></summary>
{chr(10).join(modules)}
</details>
</div>
<div class="callout takeaway"><div class="c-label">How to use this map</div><p>Before a module, skim its branch to see what's coming. After it, close the page and try to explain each topic and one connection from memory, then open the card to check yourself.</p></div>
'''


def main():
    for src in sorted(MAPS.glob("*.json")):
        data = json.loads(src.read_text(encoding="utf-8"))
        out = ROOT / "src" / data["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page_html(data), encoding="utf-8", newline="\n")
        print(f"{src.name} -> src/{data['path']}")


if __name__ == "__main__":
    main()
