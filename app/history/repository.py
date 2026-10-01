import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path


class HistoryRepository(ABC):
    @abstractmethod
    def add(self, conversation_id: str, role: str, content: str) -> None: ...

    @abstractmethod
    def last(self, conversation_id: str, n: int) -> list[dict]:
        """Últimos n mensajes en orden cronológico."""

    @abstractmethod
    def all(self, conversation_id: str) -> list[dict]: ...

    @abstractmethod
    def delete(self, conversation_id: str) -> None: ...


class SqliteHistoryRepository(HistoryRepository):
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.lock = threading.Lock()
        with self.lock:
            self.db.execute("""CREATE TABLE IF NOT EXISTS messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT NOT NULL,
                role TEXT NOT NULL, content TEXT NOT NULL, created_at REAL NOT NULL)""")
            self.db.execute("CREATE INDEX IF NOT EXISTS ix_conv ON messages(conversation_id, id)")
            self.db.commit()

    def add(self, conversation_id, role, content):
        with self.lock:
            self.db.execute("INSERT INTO messages(conversation_id, role, content, created_at) VALUES(?,?,?,?)",
                            (conversation_id, role, content, time.time()))
            self.db.commit()

    def last(self, conversation_id, n):
        if n <= 0:
            return []
        with self.lock:
            rows = self.db.execute(
                "SELECT role, content FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?",
                (conversation_id, n)).fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    def all(self, conversation_id):
        with self.lock:
            rows = self.db.execute(
                "SELECT role, content FROM messages WHERE conversation_id=? ORDER BY id",
                (conversation_id,)).fetchall()
        return [{"role": r, "content": c} for r, c in rows]

    def delete(self, conversation_id):
        with self.lock:
            self.db.execute("DELETE FROM messages WHERE conversation_id=?", (conversation_id,))
            self.db.commit()
