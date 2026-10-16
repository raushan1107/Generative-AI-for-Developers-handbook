"""Module 07: a small agent loop you can read in one sitting.
The model plans the next step by asking for a tool; our code decides whether and how it runs.
Built in: a step budget, loop detection, human approval for write tools, idempotency keys
for writes, and a trace of every step. Frameworks add more, but they all do these things."""
import json
import time
import uuid
from dataclasses import dataclass, field

from llm_tools import TOOL_EXTRAS


@dataclass
class Step:
    n: int
    tool: str
    arguments: str
    result: str
    ms: int
    status: str = "ok"            # ok | error | rejected | repeated


@dataclass
class RunResult:
    answer: str
    steps: list[Step] = field(default_factory=list)
    stopped: str | None = None    # None when the model finished; else why we stopped it
    llm_calls: int = 0
    tokens: int = 0


class Agent:
    def __init__(self, client, model, kit, system, max_steps=8, write_tools=(), approve=None, on_step=None):
        """approve(name, arguments, context) -> (ok, reason). Without it, write tools are refused."""
        self.client, self.model, self.kit, self.system = client, model, kit, system
        self.max_steps, self.write_tools, self.approve = max_steps, set(write_tools), approve
        self.on_step = on_step or (lambda step: None)

    def run(self, task: str, context: dict, history=None) -> RunResult:
        messages = [{"role": "system", "content": self.system}, *(history or []), {"role": "user", "content": task}]
        result, seen = RunResult(answer=""), {}
        for _ in range(self.max_steps):
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, tools=self.kit.schemas(), parallel_tool_calls=False, **TOOL_EXTRAS)
            result.llm_calls += 1
            result.tokens += getattr(response.usage, "total_tokens", 0) or 0
            msg = response.choices[0].message
            if not msg.tool_calls:                               # the model has finished
                result.answer = (msg.content or "").strip()
                return result
            messages.append({"role": "assistant", "content": msg.content, "tool_calls": [
                {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in msg.tool_calls]})
            for call in msg.tool_calls:
                step = self._execute(len(result.steps) + 1, call.function.name, call.function.arguments, context, seen)
                result.steps.append(step)
                self.on_step(step)
                messages.append({"role": "tool", "tool_call_id": call.id, "content": step.result})
                if step.status == "repeated" and seen[(step.tool, step.arguments)] > 3:
                    result.stopped = "loop"
                    result.answer = "Sorry, I got stuck repeating the same step. I've stopped; please contact support."
                    return result
        result.stopped = "max_steps"
        result.answer = "Sorry, that needed more steps than I'm allowed. Shall I raise a case for the support team?"
        return result

    def _execute(self, n, name, arguments, context, seen) -> Step:
        start = time.perf_counter()
        key = (name, arguments)
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 2:                                        # same call, same arguments, again
            result, status = json.dumps({"error": "you already made this exact call; use its result, "
                                                  "try something different, or answer"}), "repeated"
        elif name in self.write_tools:
            ok, reason = self.approve(name, arguments, context) if self.approve else (False, "no approver configured")
            if ok:
                # One idempotency key per approved action: if anything retries it, it runs once.
                result = self.kit.dispatch(name, arguments, context | {"idempotency_key": uuid.uuid4().hex})
                status = "error" if result.startswith('{"error"') else "ok"
            else:
                result, status = json.dumps({"error": f"the customer did not approve this action: {reason}"}), "rejected"
        else:
            result = self.kit.dispatch(name, arguments, context)
            status = "error" if result.startswith('{"error"') else "ok"
        return Step(n, name, arguments, result, int((time.perf_counter() - start) * 1000), status)


def print_step(step: Step):
    """A trace line per step: the agent's work, visible."""
    mark = {"ok": "✓", "error": "✗", "rejected": "⊘", "repeated": "↻"}[step.status]
    print(f"  {step.n}. {mark} {step.tool}({step.arguments}) -> {step.result[:110]}  [{step.ms} ms]")
