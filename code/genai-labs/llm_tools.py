"""Module 04 helper: extra arguments for requests that send tools.
Some reasoning models (for example the gpt-5.x family on Chat Completions) reject tools unless
reasoning effort is "none". Set TOOLS_REASONING_EFFORT=none in .env if a tool drill fails with
"Function tools with reasoning_effort are not supported"."""
import os

import llm  # noqa: F401  (loads .env)

_effort = os.getenv("TOOLS_REASONING_EFFORT", "").strip()
TOOL_EXTRAS = {"reasoning_effort": _effort} if _effort else {}
