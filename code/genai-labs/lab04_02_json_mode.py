"""Drill 04.2: JSON mode. The reply is always valid JSON, but which keys and types?
Run:  python lab04_02_json_mode.py            (loose prompt)
      python lab04_02_json_mode.py --tight    (prompt that lists the exact keys)"""
import json
import sys
from collections import Counter

from llm import MODEL, get_client

MESSAGES = [
    "Hi, I'm Mei, customer RR-10293. I was charged twice for a $412 flight and I fly on Friday!",
    "Can you refund the $29 overdraft fee on RR-20877? It was a one-off.",
    "My card was stolen at the station an hour ago. Diego",
    "Hola, soy Asha, cliente RR-31002. Mi transferencia lleva cinco días pendiente.",
    "There's a $640 payment to an online casino that I never made.",
]

LOOSE = "Extract the useful details from this bank customer's message as JSON."
TIGHT = """Extract details from this bank customer's message.
Return a JSON object with exactly these keys:
"customer_name" (string or null), "customer_id" (string or null),
"category" (one of card, dispute, fraud, fees, transfers, loans, account, other),
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
