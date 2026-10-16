"""Drill 07.5: agent state and memory, offline.  Run:  pytest -q test_memory.py"""
from memory import CustomerMemory, TaskState, trim_history


def test_task_state_survives_a_restart(tmp_path):
    state = TaskState("t1", goal="dispute Mei's duplicate airline charge", facts={"txn_id": "TX-1002"},
                      pending={"tool": "open_dispute", "preview": "Dispute $412.00 to SkyHigh Airlines"}, status="waiting")
    state.save(tmp_path)
    again = TaskState.load("t1", tmp_path)
    assert again == state and again.status == "waiting" and again.pending["tool"] == "open_dispute"


def test_memory_remembers_recalls_and_forgets(tmp_path):
    memory = CustomerMemory(tmp_path / "memory.json")
    assert memory.remember("RR-10293", "Prefers  email over phone calls")["status"] == "remembered"
    assert memory.remember("RR-10293", "prefers email over phone calls")["status"] == "already remembered"
    assert CustomerMemory(tmp_path / "memory.json").recall("RR-10293") == ["Prefers email over phone calls"]   # persisted
    assert memory.recall("RR-20877") == []                                                          # per customer
    assert "email" in memory.as_prompt("RR-10293") and memory.as_prompt("RR-20877") == ""
    assert memory.forget("RR-10293", "email") == 1 and memory.recall("RR-10293") == []


def test_memory_refuses_sensitive_data(tmp_path):
    memory = CustomerMemory(tmp_path / "memory.json")
    assert "error" in memory.remember("RR-10293", "Card 4111 1111 1111 1111 for future payments")
    assert "error" in memory.remember("RR-10293", "My password is hunter2")
    assert memory.recall("RR-10293") == []


def test_memory_is_small_on_purpose(tmp_path):
    memory = CustomerMemory(tmp_path / "memory.json")
    for i in range(25):
        memory.remember("RR-10293", f"fact number {i}")
    facts = memory.recall("RR-10293")
    assert len(facts) == 20 and facts[0] == "fact number 5"


def test_trim_history_summarises_older_turns():
    messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(10)]
    trimmed = trim_history(messages, keep_last=4, summarize=lambda text: f"{text.count(chr(10)) + 1} older messages")
    assert trimmed[0] == {"role": "system", "content": "Summary of the earlier conversation: 6 older messages"}
    assert trimmed[1:] == messages[-4:]
    assert trim_history(messages, keep_last=4) == messages[-4:]
    assert trim_history(messages[:3], keep_last=4) == messages[:3]
