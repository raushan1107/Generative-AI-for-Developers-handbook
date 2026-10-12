"""Drill 04.2: JSON mode. The reply is always valid JSON, but which keys and types?
Run:  python lab04_02_json_mode.py            (loose prompt)
      python lab04_02_json_mode.py --tight    (prompt that lists the exact keys)"""
import json
import sys
from collections import Counter

from llm import MODEL, get_client

MESSAGES = [
    "Hi, I'm Mei. My lab for TC-10293 says quota exceeded and my exam is on Friday!",
    "Can I get a refund for TC-20877? I can't attend next week.",
    "Where is my AZ-104 exam voucher? I finished the course 5 days ago. Diego",
    "Hola, ¿puedo cambiar la fecha de mi curso? Soy Asha, inscripción TC-31002.",
    "My certificate says Omar Farouk but my name is Omar Faruk.",
]

LOOSE = "Extract the useful details from this support message as JSON."
TIGHT = """Extract details from this support message.
Return a JSON object with exactly these keys:
"learner_name" (string or null), "enrolment_id" (string or null),
"category" (one of scheduling, billing, exam_voucher, certificate, lab_access, account, other),
"urgent" (true or false)."""


def main():
    client = get_client()
    system = TIGHT if "--tight" in sys.argv else LOOSE
    shapes = Counter()

    for text in MESSAGES:
        response = client.chat.completions.create(
            model=MODEL,
            # JSON mode: the model must produce valid JSON. The prompt must mention "JSON".
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system}, {"role": "user", "content": text}],
        )
        data = json.loads(response.choices[0].message.content)      # never fails in JSON mode...
        keys = tuple(sorted(data))
        shapes[keys] += 1
        print(json.dumps(data, ensure_ascii=False))

    print("\nDifferent key sets seen:", len(shapes))
    for keys, count in shapes.most_common():
        print(f"  {count} x {list(keys)}")


if __name__ == "__main__":
    main()
