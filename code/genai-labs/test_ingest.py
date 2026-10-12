"""Drill 06.3 and 06.4: ingestion and chunking, offline.  Run:  pytest -q test_ingest.py"""
from ingest import Doc, load_csv_faq, load_folder, load_html, load_text
from rag_chunks import chunk

PAGE = """<html><head><title>x</title><script>track()</script></head><body>
<nav><a href="/">Home</a> Sign out</nav><main><h1>Lab rules</h1><p>Intro &amp; scope.</p>
<h2>Limits</h2><ul><li>Four hours idle</li><li>Two VMs</li></ul></main><footer>&copy; 2026 · 1,204 views</footer></body></html>"""


def test_html_keeps_content_and_drops_page_chrome(tmp_path):
    (tmp_path / "rules.html").write_text(PAGE, encoding="utf-8")
    title, text = load_html(tmp_path / "rules.html")
    assert title == "Lab rules"
    assert "## Limits" in text and "- Four hours idle" in text and "Intro & scope." in text
    assert not any(junk in text for junk in ("Home", "Sign out", "track()", "views"))


def test_text_upper_case_lines_become_sections(tmp_path):
    (tmp_path / "runbook.txt").write_text("LAB RUNBOOK\nOwner: Ops.\n\nLAB-409 QUOTA ERRORS\nNot incidents.\n",
                                          encoding="utf-8")
    title, text = load_text(tmp_path / "runbook.txt")
    assert title == "Lab runbook" and "## LAB-409 quota errors\nNot incidents." in text


def test_csv_rows_become_sections(tmp_path):
    (tmp_path / "staff-faq.csv").write_text('question,answer\nCan I?,"Yes, once."\nEmpty row,\n', encoding="utf-8")
    title, text = load_csv_faq(tmp_path / "staff-faq.csv")
    assert title == "Staff FAQ" and text.count("## ") == 1 and "## Can I?\nYes, once." in text


def test_folder_report_skips_duplicates_unsupported_and_empty(tmp_path):
    body = "# Policy\n\n## Rule\nRefunds take 5 to 10 business days."
    (tmp_path / "policy.md").write_text(body, encoding="utf-8")
    (tmp_path / "policy_FINAL.md").write_bytes((body.replace("\n", "\r\n") + "\r\n\r\n").encode())  # same after cleaning
    (tmp_path / "logo.png").write_bytes(b"\x89PNG")
    (tmp_path / "blank.md").write_text("# Blank\n", encoding="utf-8")
    docs, report = load_folder(tmp_path, "staff")
    assert [d.id for d in docs] == ["policy"] and docs[0].audience == "staff"
    assert dict(report) == {"blank.md": "skipped: empty", "logo.png": "skipped: unsupported format",
                            "policy.md": "loaded: 1 sections, 53 chars",
                            "policy_FINAL.md": "skipped: duplicate of policy.md"}


def test_chunks_keep_intro_header_source_and_audience():
    doc = Doc("refunds", "Refunds", "# Refunds\nThe start date is day one.\n\n## How much\n- 14+ days: 100%\n- 7-13 days: 50%",
              "refunds.md", "public")
    first, second = chunk(doc)
    assert first["id"] == "refunds#1" and first["title"] == "Refunds > Overview" and "start date" in first["text"]
    assert second["text"] == "Refunds > How much\n- 14+ days: 100%\n- 7-13 days: 50%"
    assert second["source"] == "refunds.md" and second["audience"] == "public"


def test_long_sections_split_at_paragraphs_and_keep_the_header():
    para = "word " * 50
    doc = Doc("d", "Doc", f"# Doc\n## Long\n{para}\n\n{para}\n\n{para}", "d.md", "public")
    pieces = chunk(doc, max_chars=600)
    assert len(pieces) == 2 and all(p["text"].startswith("Doc > Long\n") for p in pieces)
    assert all(len(p["text"]) <= 600 + len("Doc > Long\n") for p in pieces)
