"""SQLite-backed todo storage for the Todo widget."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from platformdirs import user_state_dir

APP_NAME = "termdash"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    notes TEXT,
    due_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def todo_db_path() -> Path:
    """Return the default todo database path for the current platform."""
    return Path(user_state_dir(APP_NAME, appauthor=False)) / "todo.db"


@dataclass(frozen=True)
class TodoItem:
    """One persisted todo."""

    id: int
    title: str
    notes: str | None
    due_date: str | None
    created_at: str
    updated_at: str


class TodoStore:
    """Create, read, and delete todos in a local SQLite database.

    Every method opens and closes its own connection so no file handle
    outlives the call, which keeps deletion safe on Windows.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.is_file()

    def initialise(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        try:
            connection.execute(_SCHEMA)
            connection.commit()
        finally:
            connection.close()

    def list_todos(self) -> list[TodoItem]:
        if not self.exists():
            return []
        rows = self._query(
            "SELECT id, title, notes, due_date, created_at, updated_at "
            "FROM todos ORDER BY id"
        )
        return [TodoItem(*row) for row in rows]

    def get_todo(self, todo_id: int) -> TodoItem | None:
        if not self.exists():
            return None
        rows = self._query(
            "SELECT id, title, notes, due_date, created_at, updated_at "
            "FROM todos WHERE id = ?",
            (todo_id,),
        )
        return TodoItem(*rows[0]) if rows else None

    def create_todo(
        self, title: str, notes: str | None, due_date: str | None
    ) -> int:
        self._validate(title)
        self.initialise()
        timestamp = self._timestamp()
        connection = sqlite3.connect(self.path)
        try:
            cursor = connection.execute(
                "INSERT INTO todos (title, notes, due_date, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (title, notes, due_date, timestamp, timestamp),
            )
            connection.commit()
            row_id = cursor.lastrowid
            if row_id is None:
                raise RuntimeError("insert did not return a row id")
            return int(row_id)
        finally:
            connection.close()

    def update_todo(
        self, todo_id: int, title: str, notes: str | None, due_date: str | None
    ) -> None:
        self._validate(title)
        self._execute(
            "UPDATE todos SET title = ?, notes = ?, due_date = ?, updated_at = ? "
            "WHERE id = ?",
            (title, notes, due_date, self._timestamp(), todo_id),
        )

    def delete_todo(self, todo_id: int) -> None:
        self._execute("DELETE FROM todos WHERE id = ?", (todo_id,))

    def delete_database(self) -> None:
        self.path.unlink(missing_ok=True)

    @staticmethod
    def _validate(title: str) -> None:
        if not title or not title.strip():
            raise ValueError("Todo title must not be blank")

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(UTC).isoformat(timespec="seconds")

    def _execute(self, sql: str, params: tuple = ()) -> None:
        connection = sqlite3.connect(self.path)
        try:
            connection.execute(sql, params)
            connection.commit()
        finally:
            connection.close()

    def _query(self, sql: str, params: tuple = ()) -> list[tuple]:
        connection = sqlite3.connect(self.path)
        try:
            cursor = connection.execute(sql, params)
            return list(cursor.fetchall())
        finally:
            connection.close()
