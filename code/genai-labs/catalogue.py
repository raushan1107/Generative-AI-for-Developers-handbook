"""The TrainCrest course catalogue (fictional), used by Module 04 and 05 drills."""
import json
from pathlib import Path

COURSES = json.loads((Path(__file__).parent / "data" / "courses.json").read_text(encoding="utf-8"))


def find_courses(level=None, max_price_usd=None, course_format=None, text=None):
    """Plain keyword filter over the catalogue: the kind of function your app already has."""
    hits = []
    for c in COURSES:
        if level and c["level"] != level:
            continue
        if max_price_usd is not None and c["price_usd"] > max_price_usd:
            continue
        if course_format and c["format"] != course_format:
            continue
        if text and text.lower() not in (c["title"] + " " + c["description"]).lower():
            continue
        hits.append({k: c[k] for k in ("id", "title", "level", "format", "price_usd")})
    return hits


def get_course(course_id):
    return next((c for c in COURSES if c["id"] == course_id.upper()), None)
