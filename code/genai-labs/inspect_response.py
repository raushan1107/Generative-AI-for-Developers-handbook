"""Drill 02.4 (reference solution): print the fields that matter from a saved chat completion."""
import json
import sys
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else "response.json")
data = json.loads(path.read_text(encoding="utf-8"))

if "error" in data:
    print("ERROR:", data["error"].get("code"), "-", data["error"].get("message"))
    sys.exit(1)

choice = data["choices"][0]
usage = data.get("usage") or {}
details = usage.get("completion_tokens_details") or {}

print(f"model            {data.get('model')}")
print(f"finish_reason    {choice.get('finish_reason')}")
print(f"answer           {(choice['message'].get('content') or '')[:200]}")
print(f"tokens in / out  {usage.get('prompt_tokens')} / {usage.get('completion_tokens')}")
print(f"reasoning tokens {details.get('reasoning_tokens', 0)}")

filters = choice.get("content_filter_results")
if filters:
    flagged = [name for name, result in filters.items() if isinstance(result, dict) and result.get("filtered")]
    print(f"content filter   {'flagged: ' + ', '.join(flagged) if flagged else 'nothing filtered'}")
