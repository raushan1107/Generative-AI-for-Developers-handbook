"""Drill 06.3: ingest TrainCrest's knowledge base: public help articles and internal staff documents
in four formats. Look at what the loaders keep, drop and skip."""

from ingest import DATA, load_folder

total = []
for folder, audience in (("help", "public"), ("internal", "staff")):
    docs, report = load_folder(DATA / folder, audience)
    total += docs
    print(f"\n{folder}/  (audience: {audience})")
    for name, outcome in report:
        print(f"  {name:32} {outcome}")

wiki = next(d for d in total if d.id == "exception-approvals")
raw = (DATA / "internal" / wiki.source).read_text(encoding="utf-8")
print(f"\n{len(total)} documents. The wiki page: {len(raw)} characters of HTML -> {len(wiki.text)} of text:\n")
print(wiki.text[:420] + " ...")
