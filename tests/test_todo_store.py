"""Unit tests for the SQLite todo store."""

from pathlib import Path

import pytest

from termdash.storage.todo_store import TodoStore, todo_db_path


def test_default_path_is_platform_specific(tmp_path: Path):
    path = todo_db_path()
    assert path.name == "todo.db"
    assert "termdash" in str(path).lower()


def test_reading_a_missing_database_does_not_create_it(tmp_path: Path):
    store = TodoStore(tmp_path / "todo.db")

    assert not store.exists()
    assert store.list_todos() == []
    assert store.get_todo(1) is None
    assert not store.exists()


def test_create_and_list_in_insertion_order(tmp_path: Path):
    store = TodoStore(tmp_path / "todo.db")

    first = store.create_todo("First", None, None)
    second = store.create_todo("Second", "Notes", "2026-08-24")

    todos = store.list_todos()
    assert [todo.id for todo in todos] == [first, second]
    assert todos[0].title == "First"
    assert todos[1].notes == "Notes"
    assert todos[1].due_date == "2026-08-24"
    assert todos[1].created_at


def test_get_todo_returns_item_or_none(tmp_path: Path):
    store = TodoStore(tmp_path / "todo.db")
    todo_id = store.create_todo("Only", None, None)

    found = store.get_todo(todo_id)
    assert found is not None
    assert found.title == "Only"
    assert store.get_todo(999) is None


def test_blank_titles_are_rejected(tmp_path: Path):
    store = TodoStore(tmp_path / "todo.db")

    with pytest.raises(ValueError, match="blank"):
        store.create_todo("", None, None)
    with pytest.raises(ValueError, match="blank"):
        store.create_todo("   ", None, None)
    with pytest.raises(ValueError, match="blank"):
        store.create_todo("Real", None, None)
        store.update_todo(0, "  ", None, None)


def test_update_rewrites_all_fields(tmp_path: Path):
    store = TodoStore(tmp_path / "todo.db")
    todo_id = store.create_todo("Old", "Old notes", "2026-01-01")

    store.update_todo(todo_id, "New", None, None)
    updated = store.get_todo(todo_id)

    assert updated is not None
    assert updated.title == "New"
    assert updated.notes is None
    assert updated.due_date is None


def test_update_a_missing_todo_is_a_no_op(tmp_path: Path):
    store = TodoStore(tmp_path / "todo.db")
    store.create_todo("Kept", None, None)

    store.update_todo(999, "Ghost", None, None)

    assert [todo.title for todo in store.list_todos()] == ["Kept"]


def test_delete_removes_only_the_target(tmp_path: Path):
    store = TodoStore(tmp_path / "todo.db")
    keep = store.create_todo("Keep", None, None)
    gone = store.create_todo("Gone", None, None)

    store.delete_todo(gone)

    assert [todo.id for todo in store.list_todos()] == [keep]


def test_delete_database_after_read(tmp_path: Path):
    store = TodoStore(tmp_path / "todo.db")
    store.create_todo("Doomed", None, None)
    store.list_todos()

    store.delete_database()

    assert not store.exists()
    assert store.list_todos() == []


def test_unicode_titles_roundtrip(tmp_path: Path):
    store = TodoStore(tmp_path / "todo.db")
    store.create_todo("買牛奶 — café ☕", "Ünïcode notes", None)

    todo = store.list_todos()[0]
    assert todo.title == "買牛奶 — café ☕"
    assert todo.notes == "Ünïcode notes"
