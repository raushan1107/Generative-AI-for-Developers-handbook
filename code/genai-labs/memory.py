"""Module 07: state and memory for agents, three kinds:
- TaskState: short-term working state of one multi-step task (goal, facts, steps, a pending
  approval), saved as JSON so the task can pause, for example while a human decides, and resume.
- LearnerMemory: long-term memory, small facts a learner asked us to remember, recalled at the
  start of each session. Explicit, inspectable and deletable, and it refuses sensitive data.
- trim_history: keep a long conversation within budget by summarising its older turns."""
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

STATE_DIR = Path(__file__).parent / "data" / "agent_state"
SENSITIVE = re.compile(r"\b(?:\d[ -]?){13,19}\b|password|passcode|\bcvv\b|\bpin\b", re.I)


@dataclass
class TaskState:
    task_id: str
    goal: str
    facts: dict = field(default_factory=dict)         # what the agent has found out so far
    done: list = field(default_factory=list)          # steps completed, in order
    pending: dict | None = None                       # an action waiting for a human's decision
    status: str = "running"                           # running | waiting | finished | failed

    def save(self, folder=STATE_DIR):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{self.task_id}.json").write_text(json.dumps(asdict(self), indent=1), encoding="utf-8")

    @classmethod
    def load(cls, task_id, folder=STATE_DIR):
        return cls(**json.loads((Path(folder) / f"{task_id}.json").read_text(encoding="utf-8")))


class LearnerMemory:
    MAX_FACTS = 20

    def __init__(self, path=STATE_DIR / "memory.json"):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=1, ensure_ascii=False), encoding="utf-8")

    def remember(self, learner: str, fact: str) -> dict:
        fact = " ".join(fact.split())
        if SENSITIVE.search(fact):
            return {"error": "not stored: memory never keeps card numbers, passwords or PINs"}
        facts = self.data.setdefault(learner, [])
        if any(f["fact"].lower() == fact.lower() for f in facts):
            return {"status": "already remembered"}
        facts.append({"fact": fact, "saved": time.strftime("%Y-%m-%d")})
        del facts[:-self.MAX_FACTS]                   # oldest go first: memory is small on purpose
        self._save()
        return {"status": "remembered", "fact": fact}

    def forget(self, learner: str, containing: str) -> int:
        before = len(self.data.get(learner, []))
        self.data[learner] = [f for f in self.data.get(learner, []) if containing.lower() not in f["fact"].lower()]
        self._save()
        return before - len(self.data[learner])

    def recall(self, learner: str) -> list[str]:
        return [f["fact"] for f in self.data.get(learner, [])]

    def as_prompt(self, learner: str) -> str:
        facts = self.recall(learner)
        return "" if not facts else "Known about this learner from earlier sessions:\n" + "\n".join(f"- {f}" for f in facts)


def trim_history(messages, keep_last: int = 6, summarize=None):
    """Keep the last `keep_last` messages; replace older ones with one summary message.
    `summarize(text) -> str` is usually a cheap model call; without it, older turns are dropped."""
    if len(messages) <= keep_last:
        return list(messages)
    older, recent = messages[:-keep_last], messages[-keep_last:]
    if summarize is None:
        return list(recent)
    text = "\n".join(f"{m['role']}: {m['content']}" for m in older if m.get("content"))
    return [{"role": "system", "content": "Summary of the earlier conversation: " + summarize(text)}] + list(recent)
