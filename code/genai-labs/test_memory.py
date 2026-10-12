"""Drill 07.5: agent state and memory, offline.  Run:  pytest -q test_memory.py"""
from memory import LearnerMemory, TaskState, trim_history


def test_task_state_survives_a_restart(tmp_path):
    state = TaskState("t1", goal="move Diego's AZ-104 class", facts={"enrolment_id": "TC-20877"},
                      pending={"tool": "reschedule", "preview": "Move TC-20877 ($50)"}, status="waiting")
    state.save(tmp_path)
    again = TaskState.load("t1", tmp_path)
    assert again == state and again.status == "waiting" and again.pending["tool"] == "reschedule"


def test_memory_remembers_recalls_and_forgets(tmp_path):
    memory = LearnerMemory(tmp_path / "memory.json")
    assert memory.remember("L-MEI", "Prefers  weekend classes")["status"] == "remembered"
    assert memory.remember("L-MEI", "prefers weekend classes")["status"] == "already remembered"
    assert LearnerMemory(tmp_path / "memory.json").recall("L-MEI") == ["Prefers weekend classes"]   # persisted
    assert memory.recall("L-DIEGO") == []                                                          # per learner
    assert "weekend" in memory.as_prompt("L-MEI") and memory.as_prompt("L-DIEGO") == ""
    assert memory.forget("L-MEI", "weekend") == 1 and memory.recall("L-MEI") == []


def test_memory_refuses_sensitive_data(tmp_path):
    memory = LearnerMemory(tmp_path / "memory.json")
    assert "error" in memory.remember("L-MEI", "Card 4111 1111 1111 1111 for future payments")
    assert "error" in memory.remember("L-MEI", "My password is hunter2")
    assert memory.recall("L-MEI") == []


def test_memory_is_small_on_purpose(tmp_path):
    memory = LearnerMemory(tmp_path / "memory.json")
    for i in range(25):
        memory.remember("L-MEI", f"fact number {i}")
    facts = memory.recall("L-MEI")
    assert len(facts) == 20 and facts[0] == "fact number 5"


def test_trim_history_summarises_older_turns():
    messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(10)]
    trimmed = trim_history(messages, keep_last=4, summarize=lambda text: f"{text.count(chr(10)) + 1} older messages")
    assert trimmed[0] == {"role": "system", "content": "Summary of the earlier conversation: 6 older messages"}
    assert trimmed[1:] == messages[-4:]
    assert trim_history(messages, keep_last=4) == messages[-4:]
    assert trim_history(messages[:3], keep_last=4) == messages[:3]
