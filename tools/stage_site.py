"""Copy the public site into _site/ for GitHub Pages.

Only learner-facing files are published. Author notes (docs/), page sources
(src/), build tools (tools/) and draft modules stay in the repository but
never reach the site.

Usage (from the repo root, after `python tools/build.py`):
    python tools/stage_site.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"

PUBLIC = ["index.html", ".nojekyll", "assets", "start", "setup", "modules",
          "project", "labs", "capstone", "oss", "code"]
SKIP = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc", ".env",
                              ".venv", "usage.jsonl", "response.json")


def draft_paths():
    """Folders and files that belong to draft modules and draft sections: pages and their code."""
    nav = json.loads((ROOT / "tools" / "nav.json").read_text(encoding="utf-8"))
    paths = []
    for section in nav["sections"]:
        if section.get("draft"):
            paths += [item["path"] for item in section.get("items", [])] + section.get("code_dirs", [])
        for module in section.get("modules", []):
            if module.get("draft"):
                num = module["num"]
                paths += [f"modules/{num}", f"code/traincrest-assist/m{num}"]
    return paths


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
    files = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"Staged {files} files in _site/ (left out drafts: {', '.join(drafts) or 'none'})")


if __name__ == "__main__":
    main()
