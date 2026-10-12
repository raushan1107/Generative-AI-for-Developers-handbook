"""Tool registry and dispatcher (milestone 4; same design as Drill 04.7).
Register plain Python functions once; get strict tool schemas for the API and a safe
dispatch() that turns a model's tool call into a function call."""
import json

import openai
from pydantic import BaseModel, ValidationError


class Tool:
    def __init__(self, func, args_model, needs_context):
        self.func, self.args_model, self.needs_context = func, args_model, needs_context
        self.name = func.__name__


class Toolkit:
    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, args_model: type[BaseModel], needs_context: bool = False):
        """Decorator: @kit.register(ArgsModel) above a function whose docstring describes it."""
        def wrap(func):
            self.tools[func.__name__] = Tool(func, args_model, needs_context)
            return func
        return wrap

    def schemas(self):
        """Tool definitions to pass as tools=... (strict JSON Schema from each args model)."""
        return [openai.pydantic_function_tool(t.args_model, name=t.name, description=(t.func.__doc__ or "").strip())
                for t in self.tools.values()]

    def dispatch(self, name: str, arguments: str, context: dict | None = None) -> str:
        """Run one tool call and return a JSON string for the "tool" message.
        Problems come back as {"error": ...} so the model can recover; nothing raises."""
        tool = self.tools.get(name)
        if tool is None:
            return json.dumps({"error": f"unknown tool {name!r}"})
        try:
            args = tool.args_model.model_validate_json(arguments or "{}")
        except ValidationError as e:
            first = e.errors()[0]
            return json.dumps({"error": f"invalid arguments: {'.'.join(map(str, first['loc']))}: {first['msg']}"})
        try:
            if tool.needs_context:
                result = tool.func(args, context or {})
            else:
                result = tool.func(args)
        except PermissionError as e:
            return json.dumps({"error": f"not allowed: {e}"})
        except Exception as e:                      # a bug in a tool must not crash the chat
            return json.dumps({"error": f"tool failed: {type(e).__name__}"})
        return json.dumps(result, ensure_ascii=False, default=str)
