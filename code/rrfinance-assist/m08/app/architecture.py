"""Small, offline examples of explicit routing and expiring session storage."""

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Mapping, Sequence


def select_deployment(task: str, routes: Mapping[str, str]) -> str:
    """Resolve a task through an explicit allowlist; never accept a model name from a user."""
    if task not in routes:
        raise ValueError(f"Unconfigured task: {task}")
    deployment = routes[task].strip()
    if not deployment:
        raise ValueError(f"Empty deployment for task: {task}")
    return deployment


def new_trace_id() -> str:
    return uuid.uuid4().hex


class SessionStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    messages_json TEXT NOT NULL,
                    expires_at INTEGER NOT NULL
                )"""
            )

    def save(
        self,
        session_id: str,
        messages: Sequence[Mapping[str, str]],
        expires_at: int,
    ) -> None:
        if not session_id or expires_at <= 0:
            raise ValueError("A session ID and positive expiry are required")
        serialized = json.dumps(list(messages), separators=(",", ":"))
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """INSERT INTO sessions(session_id, messages_json, expires_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(session_id) DO UPDATE SET
                       messages_json = excluded.messages_json,
                       expires_at = excluded.expires_at""",
                (session_id, serialized, expires_at),
            )

    def delete(self, session_id: str) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "DELETE FROM sessions WHERE session_id = ?", (session_id,)
            )

    def load(
        self, session_id: str, now: int | None = None
    ) -> list[dict[str, str]] | None:
        current_time = int(time.time()) if now is None else now
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT messages_json, expires_at FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            if row[1] <= current_time:
                connection.execute(
                    "DELETE FROM sessions WHERE session_id = ?", (session_id,)
                )
                return None
        messages = json.loads(row[0])
        if not isinstance(messages, list):
            raise ValueError("Stored session must contain a message list")
        return messages
