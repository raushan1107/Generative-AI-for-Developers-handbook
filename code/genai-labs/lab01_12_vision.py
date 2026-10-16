"""Drill 01.12: one request, two modalities: a statement image plus a text question."""
import base64
import mimetypes
import sys
from pathlib import Path

from llm import get_client, MODEL

path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/statement.png")
mime = mimetypes.guess_type(path.name)[0] or "image/png"
image_b64 = base64.b64encode(path.read_bytes()).decode()

client = get_client()
response = client.chat.completions.create(
    model=MODEL,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": (
                "A customer sent this picture of their RR Finance Bank card statement and says "
                "'something is wrong here'. 1) Which line or lines look wrong, and why? "
                "2) Is this a dispute (a payment they made, charged wrongly) or fraud (a payment they "
                "didn't make)? 3) What should the agent do next? Be brief.")},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
        ],
    }],
)
print(response.choices[0].message.content)
print("\ninput tokens (text + image):", response.usage.prompt_tokens)
