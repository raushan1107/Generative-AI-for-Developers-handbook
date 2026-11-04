"""Check that the capstone's synthetic evaluation references point to report pages."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def main() -> None:
    metrics = json.loads((DATA / "expected_metrics.json").read_text(encoding="utf-8"))
    cases = json.loads((DATA / "evaluation_cases.json").read_text(encoding="utf-8"))
    reports = {
        path.stem: path.read_text(encoding="utf-8")
        for path in (DATA / "reports").glob("*.md")
    }
    if not reports:
        raise ValueError("No synthetic report files were found")
    for case in cases["cases"]:
        matching = [text for text in reports.values() if case["source_document"] in text]
        if not matching:
            raise ValueError(f"{case['id']}: source document is missing")
        if case["source_page"] is None:
            continue
        report = matching[0]
        page_heading = f"## Page {case['source_page']} —"
        if page_heading not in report:
            raise ValueError(f"{case['id']}: cited page heading is missing")
    if set(metrics["issuers"]) != {
        "northstar_payments",
        "riverstone_retail",
        "cedar_grid_systems",
    }:
        raise ValueError("Expected metrics must cover all three synthetic issuers")
    print(f"OK: {len(reports)} reports and {len(cases['cases'])} evaluation cases")


if __name__ == "__main__":
    main()
