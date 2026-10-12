"""Drill 01.12: one request, two modalities: a screenshot plus a text question."""
import base64
import mimetypes
import sys
from pathlib import Path

from llm import get_client, MODEL

path = Path(sys.argv[1] if len(sys.argv) > 1 else "screenshot.png")
mime = mimetypes.guess_type(path.name)[0] or "image/png"
image_b64 = base64.b64encode(path.read_bytes()).decode()

client = get_client()
response = client.chat.completions.create(
    model=MODEL,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": (
                "A learner sent this screenshot from a TrainCrest hands-on lab. "
                "1) What is the error? 2) What is the most likely cause? "
                "3) What should support tell the learner to try next? Be brief.")},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
        ],
    }],
)
print(response.choices[0].message.content)
print("\ninput tokens (text + image):", response.usage.prompt_tokens)
