"""Module 06 helper: check citations before anyone reads the answer.
Three cheap checks, no extra model call:
- unknown:     the answer cites [n], but there was no source n (an invented citation);
- uncited:     a sentence states a number (price, percentage, days) but cites nothing;
- unsupported: a sentence cites sources, but one of its numbers appears in none of them.
Module 09 adds model-based groundedness checks; these catch the most damaging mistakes for free."""
import re

CITE = re.compile(r"\[(\d+)\]")
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
IDS = re.compile(r"\b[A-Z]{1,3}-\d+\b")                 # codes like TC-10477 or LAB-503 are names, not amounts


def sentences(answer: str):
    """Split into sentences, keeping citations that come after the full stop ('... refund. [1]')."""
    parts = re.split(r"(?<=[.!?])\s+", answer.strip())
    out = []
    for part in parts:
        lead = re.match(r"^((?:\[\d+\])+)\s*", part)
        if lead and out:                                    # citations at the start belong to the previous sentence
            out[-1] += " " + lead.group(1)
            part = part[lead.end():]
        if part:
            out.append(part)
    return out


def numbers(text: str) -> set[str]:
    text = IDS.sub(" ", CITE.sub(" ", text))
    return {n.replace(",", "").rstrip(".") for n in NUMBER.findall(text)}


def check(answer: str, sources, question: str = "") -> dict:
    """sources[n-1] is the chunk shown to the model as [n]. Numbers the learner wrote are allowed."""
    report = {"cited": [], "unknown": [], "uncited": [], "unsupported": []}
    for sentence in sentences(answer):
        cited = [int(n) for n in CITE.findall(sentence)]
        report["cited"] += [n for n in cited if 1 <= n <= len(sources) and n not in report["cited"]]
        report["unknown"] += [n for n in cited if not 1 <= n <= len(sources)]
        amounts = numbers(sentence) - numbers(question)
        valid = [n for n in cited if 1 <= n <= len(sources)]
        if amounts and not valid:
            report["uncited"].append(sentence)
        elif valid:
            found = set().union(*(numbers(sources[n - 1]["text"]) for n in valid))
            missing = sorted(amounts - found)
            if missing:
                report["unsupported"].append({"sentence": sentence, "numbers": missing})
    report["ok"] = not (report["unknown"] or report["uncited"] or report["unsupported"])
    return report


def render(answer: str, sources, report: dict) -> str:
    """The answer without invented citation numbers, followed by the sources it actually cites."""
    clean = CITE.sub(lambda m: m.group(0) if int(m.group(1)) in report["cited"] else "", answer)
    lines = [f"[{n}] {sources[n - 1]['title']} ({sources[n - 1]['source']})" for n in sorted(report["cited"])]
    return clean.strip() + ("\n\nSources:\n" + "\n".join(lines) if lines else "")
