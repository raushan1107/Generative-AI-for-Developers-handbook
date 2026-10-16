"""Copy the public site into _site/ for GitHub Pages.

Only learner-facing files are published. Author notes (docs/), page sources
(src/), build tools (tools/) and draft modules stay in the repository but
never reach the site.

Usage (from the repo root, after `python tools/build.py`):
    python tools/stage_site.py
"""
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"

PUBLIC = ["index.html", ".nojekyll", "assets", "start", "setup", "modules",
          "project", "labs", "capstone", "oss", "maps", "code"]
SKIP = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc", ".env",
                              ".venv", "usage.jsonl", "response.json")


def draft_paths():
    """Folders and files that belong to draft modules and draft sections: pages and their code."""
    nav = json.loads((ROOT / "tools" / "nav.json").read_text(encoding="utf-8"))
    paths = []
    for section in nav["sections"]:
        if section.get("draft"):
            paths += [item["path"] for item in section.get("items", [])] + section.get("code_dirs", [])
        for item in section.get("items", []):          # a single draft item (e.g. a lab not live yet)
            if item.get("draft") and not section.get("draft"):
                paths.append(item["path"])
                for pattern in item.get("code_files", []):
                    paths += sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern))
        for module in section.get("modules", []):
            if module.get("draft"):
                num = module["num"]
                paths += [f"modules/{num}", f"code/rrfinance-assist/m{num}"]
    return paths


def zip_folder(src, target, top, keep=lambda rel: True):
    skip = {"__pycache__", ".pytest_cache", ".env", "index", "kb_index", "agent_state", ".embed_cache.json",
            "search_index.json", "kb_index.json", "chat_log.jsonl", "tickets.jsonl", "actions.jsonl"}
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob("*")):
            rel = p.relative_to(src)
            if p.is_file() and not skip & set(rel.parts) and not p.suffix == ".log" and keep(rel):
                z.write(p, Path(top) / rel)


def make_handbook_downloads(drafts):
    """genai-labs-kit.zip (helpers, data and the drill scripts of live modules) and one complete project
    zip per live milestone, rrfinance-assist-mNN.zip. A static site can't serve a folder."""
    nav = json.loads((ROOT / "tools" / "nav.json").read_text(encoding="utf-8"))
    draft_nums = {m["num"] for s in nav["sections"] for m in s.get("modules", []) if m.get("draft") or m.get("soon")}
    labs = ROOT / "code" / "genai-labs"
    zip_folder(labs, OUT / "code" / "genai-labs-kit.zip", "genai-labs",
               keep=lambda rel: not (rel.name.startswith("lab") and rel.name[3:5] in draft_nums))
    for project in sorted((ROOT / "code" / "rrfinance-assist").glob("m[0-9][0-9]")):
        if project.name[1:] not in draft_nums:
            zip_folder(project, OUT / "code" / f"rrfinance-assist-{project.name}.zip", "rrfinance-assist")


def make_lab_downloads(drafts):
    """Zips for the open-source labs (a static site can't serve a folder):
    oss-labs-data.zip (the data folder, for Lab 0) and oss-labs-complete.zip (all lab code, for catching up)."""
    src = ROOT / "code" / "oss-labs"
    if "code/oss-labs" in drafts or not src.exists():
        return
    skip = {"__pycache__", ".pytest_cache", ".env", "search_index.json", "kb_index.json", "chat_log.jsonl"}
    hidden = set(drafts)                               # code of labs that aren't live yet stays out of the zip
    files = [p for p in sorted(src.rglob("*")) if p.is_file() and not skip & set(p.relative_to(src).parts)
             and p.relative_to(ROOT).as_posix() not in hidden]
    for name, keep in (("oss-labs-data.zip", lambda r: r.parts[0] == "data"), ("oss-labs-complete.zip", lambda r: True)):
        with zipfile.ZipFile(OUT / "code" / name, "w", zipfile.ZIP_DEFLATED) as z:
            for p in files:
                rel = p.relative_to(src)
                if keep(rel):
                    z.write(p, Path("oss-genai-labs") / rel)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for name in PUBLIC:
        src = ROOT / name
        if not src.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, OUT / name, ignore=SKIP)
        else:
            shutil.copy2(src, OUT / name)
    drafts = draft_paths()
    for rel in drafts:
        target = OUT / rel
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    for folder in sorted((p for p in OUT.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
        if not any(folder.iterdir()):                 # e.g. oss/ once all its draft pages are removed
            folder.rmdir()
    make_lab_downloads(drafts)
    make_handbook_downloads(drafts)
    files = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"Staged {files} files in _site/ (left out drafts: {', '.join(drafts) or 'none'})")


if __name__ == "__main__":
    main()
