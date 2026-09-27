"""Behavioural tests for the Todo widget's menu-driven flows."""

from pathlib import Path

from conftest import run_pilot
from textual.widgets import ContentSwitcher, Input, Label, Static

from termdash.app import Termdash
from termdash.config import parse_config
from termdash.storage.todo_store import TodoStore
from termdash.widgets.todo import Todo, TodoOptionList


def todo_config(tmp_path: Path):
    database = str(tmp_path / "todo.db").replace("\\", "/")
    return parse_config(
        f'[widgets]\nkind = "todo"\nopts = {{ database = "{database}" }}\n',
        source="test",
    )


def current_view(todo: Todo) -> str | None:
    return todo.query_one("#todo-views", ContentSwitcher).current


def test_summary_offers_to_create_the_database(tmp_path):
    config = todo_config(tmp_path)

    async def scenario(pilot):
        todo = pilot.app.query_one(Todo)
        summary = str(todo.query_one("#todo-summary-list", Static).render())
        assert "No todo database yet." in summary
        assert not TodoStore(tmp_path / "todo.db").exists()

    run_pilot(Termdash(config), scenario)


def test_menu_opens_focused_and_escape_returns_to_summary(tmp_path):
    config = todo_config(tmp_path)

    async def scenario(pilot):
        todo = pilot.app.query_one(Todo)
        await pilot.click("#todo-manage")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-menu-view"
        assert todo.query_one("#todo-menu-list").has_focus
        assert "interacting" in todo.classes

        await pilot.press("escape")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-summary"
        assert "interacting" not in todo.classes

    run_pilot(Termdash(config), scenario)


def test_add_flow_persists_a_todo(tmp_path):
    config = todo_config(tmp_path)

    async def scenario(pilot):
        todo = pilot.app.query_one(Todo)
        await pilot.click("#todo-manage")
        await pilot.pause(0.1)
        await pilot.press("down", "enter")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-form-view"
        assert todo.query_one("#todo-title-input", Input).has_focus

        todo.query_one("#todo-title-input", Input).value = "Buy milk"
        todo.query_one("#todo-due-date-input", Input).value = "2026-08-24"
        await pilot.click("#todo-save")
        await pilot.pause(0.1)

        assert current_view(todo) == "todo-menu-view"
        summary = str(todo.query_one("#todo-summary-list", Static).render())
        assert "1. Buy milk — due 2026-08-24" in summary
        todos = TodoStore(tmp_path / "todo.db").list_todos()
        assert [todo_item.title for todo_item in todos] == ["Buy milk"]

    run_pilot(Termdash(config), scenario)


def test_blank_title_and_bad_date_are_rejected_in_place(tmp_path):
    config = todo_config(tmp_path)

    async def scenario(pilot):
        todo = pilot.app.query_one(Todo)
        await pilot.click("#todo-manage")
        await pilot.pause(0.1)
        await pilot.press("down", "enter")
        await pilot.pause(0.1)

        await pilot.click("#todo-save")
        await pilot.pause(0.1)
        error = str(todo.query_one("#todo-form-error", Static).render())
        assert "Title is required." in error
        assert current_view(todo) == "todo-form-view"

        todo.query_one("#todo-title-input", Input).value = "Later"
        todo.query_one("#todo-due-date-input", Input).value = "24-08-2026"
        await pilot.click("#todo-save")
        await pilot.pause(0.1)
        error = str(todo.query_one("#todo-form-error", Static).render())
        assert "Due date must use YYYY-MM-DD." in error
        assert current_view(todo) == "todo-form-view"

        assert not TodoStore(tmp_path / "todo.db").exists()

    run_pilot(Termdash(config), scenario)


def test_edit_flow_updates_the_stored_todo(tmp_path):
    database = tmp_path / "todo.db"
    store = TodoStore(database)
    store.create_todo("Old title", None, None)
    config = todo_config(tmp_path)

    async def scenario(pilot):
        todo = pilot.app.query_one(Todo)
        await pilot.click("#todo-manage")
        await pilot.pause(0.1)
        await pilot.press("down", "down", "enter")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-selector-view"

        await pilot.press("enter")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-form-view"
        assert todo.query_one("#todo-title-input", Input).value == "Old title"

        todo.query_one("#todo-title-input", Input).value = "New title"
        await pilot.click("#todo-save")
        await pilot.pause(0.1)

        summary = str(todo.query_one("#todo-summary-list", Static).render())
        assert "New title" in summary
        assert TodoStore(database).list_todos()[0].title == "New title"

    run_pilot(Termdash(config), scenario)


def test_delete_flow_requires_confirmation(tmp_path):
    database = tmp_path / "todo.db"
    store = TodoStore(database)
    keep = store.create_todo("Keep", None, None)
    store.create_todo("Gone", None, None)
    config = todo_config(tmp_path)

    async def scenario(pilot):
        todo = pilot.app.query_one(Todo)
        await pilot.click("#todo-manage")
        await pilot.pause(0.1)
        await pilot.press("down", "down", "down", "enter")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-selector-view"

        await pilot.press("down", "enter")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-delete-view"
        assert TodoStore(database).list_todos()[1].title == "Gone"

        await pilot.click("#todo-delete")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-menu-view"
        assert [t.id for t in TodoStore(database).list_todos()] == [keep]

    run_pilot(Termdash(config), scenario)


def test_delete_cancel_keeps_the_todo(tmp_path):
    database = tmp_path / "todo.db"
    store = TodoStore(database)
    store.create_todo("Safe", None, None)
    config = todo_config(tmp_path)

    async def scenario(pilot):
        todo = pilot.app.query_one(Todo)
        await pilot.click("#todo-manage")
        await pilot.pause(0.1)
        await pilot.press("down", "down", "down", "enter")
        await pilot.pause(0.1)
        await pilot.press("enter")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-delete-view"

        await pilot.click("#todo-delete-cancel")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-selector-view"
        assert TodoStore(database).list_todos()[0].title == "Safe"

    run_pilot(Termdash(config), scenario)


def test_clear_database_destroys_everything(tmp_path):
    database = tmp_path / "todo.db"
    store = TodoStore(database)
    store.create_todo("One", None, None)
    store.create_todo("Two", None, None)
    config = todo_config(tmp_path)

    async def scenario(pilot):
        todo = pilot.app.query_one(Todo)
        await pilot.click("#todo-manage")
        await pilot.pause(0.1)
        await pilot.press("down", "down", "down", "down", "enter")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-clear-view"

        await pilot.click("#todo-clear")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-summary"
        assert not TodoStore(database).exists()
        summary = str(todo.query_one("#todo-summary-list", Static).render())
        assert "No todo database yet." in summary

    run_pilot(Termdash(config), scenario)


def test_vim_keys_move_the_menu_highlight(tmp_path):
    config = todo_config(tmp_path)

    async def scenario(pilot):
        todo = pilot.app.query_one(Todo)
        await pilot.click("#todo-manage")
        await pilot.pause(0.1)
        menu = todo.query_one("#todo-menu-list", TodoOptionList)
        assert menu.highlighted == 0

        await pilot.press("j")
        await pilot.pause(0.1)
        assert menu.highlighted == 1

        await pilot.press("G")
        await pilot.pause(0.1)
        assert menu.highlighted == len(menu.options) - 1

        await pilot.press("g")
        await pilot.pause(0.1)
        assert menu.highlighted == 0

    run_pilot(Termdash(config), scenario)


def test_max_items_caps_the_summary(tmp_path):
    database = tmp_path / "todo.db"
    store = TodoStore(database)
    for number in range(1, 5):
        store.create_todo(f"Task {number}", None, None)
    db = str(database).replace("\\", "/")
    config = parse_config(
        f'[widgets]\nkind = "todo"\nopts = {{ database = "{db}", max_items = 2 }}\n',
        source="test",
    )

    async def scenario(pilot):
        todo = pilot.app.query_one(Todo)
        summary = str(todo.query_one("#todo-summary-list", Static).render())
        assert "Task 1" in summary
        assert "Task 2" in summary
        assert "Task 3" not in summary
        assert "... and 2 more" in summary

    run_pilot(Termdash(config), scenario)


def test_browse_flow_shows_detail_then_returns(tmp_path):
    database = tmp_path / "todo.db"
    store = TodoStore(database)
    store.create_todo("Inspect me", "With notes", "2026-12-31")
    config = todo_config(tmp_path)

    async def scenario(pilot):
        todo = pilot.app.query_one(Todo)
        await pilot.click("#todo-manage")
        await pilot.pause(0.1)
        await pilot.press("enter")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-selector-view"

        await pilot.press("enter")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-detail-view"
        detail = str(todo.query_one("#todo-detail-content", Static).render())
        assert "Inspect me" in detail
        assert "2026-12-31" in detail
        assert "With notes" in detail

        await pilot.click("#todo-detail-back")
        await pilot.pause(0.1)
        assert current_view(todo) == "todo-selector-view"
        assert todo.query_one("#todo-selector-title", Label)

    run_pilot(Termdash(config), scenario)


def test_selector_shows_disabled_empty_state(tmp_path):
    config = todo_config(tmp_path)

    async def scenario(pilot):
        todo = pilot.app.query_one(Todo)
        await pilot.click("#todo-manage")
        await pilot.pause(0.1)
        await pilot.press("enter")
        await pilot.pause(0.1)
        selector = todo.query_one("#todo-selector-list", TodoOptionList)
        assert selector.options[0].disabled
        assert selector.options[0].prompt == "No todos available"

    run_pilot(Termdash(config), scenario)
