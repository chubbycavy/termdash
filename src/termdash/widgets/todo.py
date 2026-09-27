"""Persistent todo widget with an in-tile multi-view interface."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalGroup, Vertical, VerticalGroup, VerticalScroll
from textual.widgets import (
    Button,
    ContentSwitcher,
    Input,
    Label,
    OptionList,
    Static,
    TextArea,
)
from textual.widgets.option_list import Option

from termdash.storage.todo_store import TodoItem, TodoStore, todo_db_path
from termdash.widgets.common import TILE_CSS
from termdash.widgets.registry import register

MENU_HINT = "j/k move · g/G first/last · l/Enter select · Esc back"


class TodoOptions(BaseModel):
    """Options for the todo widget."""

    model_config = ConfigDict(extra="forbid")

    max_items: int = Field(default=10, ge=1, le=200)
    database: str | None = None


class TodoOptionList(OptionList):
    """An option list with Vim-inspired movement shortcuts."""

    BINDINGS = [
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
        Binding("g", "first", show=False),
        Binding("G", "last", show=False),
        Binding("l", "select", show=False),
    ]

    def on_show(self) -> None:
        """Receive keyboard navigation whenever the surrounding view opens."""
        if self.highlighted is None:
            for index, option in enumerate(self.options):
                if not option.disabled:
                    self.highlighted = index
                    break
        self.focus()


class TodoTitleInput(Input):
    """Focus the title field whenever the todo form opens."""

    def on_show(self) -> None:
        """Direct typing to the mandatory field first."""
        self.focus()


@register("todo", TodoOptions)
class Todo(VerticalGroup):
    """A persistent todo list with browse, add, edit, and delete flows."""

    BINDINGS = [Binding("escape", "back", show=False)]

    max_items = 10
    database: str | None = None
    pending_action: str | None = None
    selected_todo_id: int | None = None

    DEFAULT_CSS = f"""
    Todo {{
        {TILE_CSS}
    }}

    Todo.interacting {{
        border: round $warning;
    }}

    Todo ContentSwitcher,
    Todo .todo-view {{
        width: 100%;
        height: 100%;
    }}

    Todo .todo-view {{
        padding: 1;
    }}

    Todo .todo-list {{
        height: 1fr;
        border: tall $border;
        padding: 0 1;
    }}

    Todo .todo-menu,
    Todo .todo-selector {{
        height: 1fr;
    }}

    Todo .todo-title {{
        text-style: bold;
        text-align: center;
        margin: 0 0 1 0;
    }}

    Todo .todo-actions {{
        height: auto;
        margin: 1 0 0 0;
    }}

    Todo .todo-actions Button {{
        width: 1fr;
    }}

    Todo .todo-form-actions {{
        height: auto;
        margin: 1 0 0 0;
    }}

    Todo .todo-form-actions Button {{
        width: 1fr;
    }}

    Todo .todo-message,
    Todo .todo-error,
    Todo .todo-key-hint {{
        text-align: center;
    }}

    Todo .todo-error {{
        color: $error;
        height: 1;
    }}

    Todo .todo-key-hint {{
        color: $text-muted;
        height: 1;
        margin: 1 0 0 0;
    }}

    Todo .todo-warning {{
        color: $warning;
        text-style: bold;
        text-align: center;
        border: round $warning;
        padding: 1;
        margin: 1 0;
    }}

    Todo TextArea {{
        height: 6;
        margin: 1 0;
    }}

    Todo Input {{
        margin: 1 0 0 0;
    }}

    Todo .caption {{
        width: 100%;
        height: 1;
        text-align: center;
        color: $text-muted;
        text-style: bold;
        margin: 1 0 0 0;
    }}
    """

    @property
    def store(self) -> TodoStore:
        """Return a short-lived store for the configured database path."""
        if self.database:
            return TodoStore(Path(self.database).expanduser())
        return TodoStore(todo_db_path())

    def compose(self) -> ComposeResult:
        with ContentSwitcher(initial="todo-summary", id="todo-views"):
            with Vertical(id="todo-summary", classes="todo-view"):
                yield Label("Todos", classes="todo-title")
                with VerticalScroll(classes="todo-list"):
                    yield Static(id="todo-summary-list", markup=False)
                with Vertical(classes="todo-actions"):
                    yield Button("Manage todos", id="todo-manage")

            with Vertical(id="todo-menu-view", classes="todo-view"):
                yield Label("Todo menu", classes="todo-title")
                yield TodoOptionList(
                    Option("Browse todos", id="browse"),
                    Option("Add todo", id="add"),
                    Option("Edit todo", id="edit"),
                    Option("Delete todo", id="delete"),
                    Option("Clear database", id="clear"),
                    Option("Back", id="exit"),
                    id="todo-menu-list",
                    classes="todo-menu",
                )
                yield Label(MENU_HINT, classes="todo-key-hint", markup=False)

            with Vertical(id="todo-selector-view", classes="todo-view"):
                yield Label(
                    "Select todo", id="todo-selector-title", classes="todo-title"
                )
                yield TodoOptionList(
                    id="todo-selector-list", classes="todo-selector"
                )
                yield Label(MENU_HINT, classes="todo-key-hint", markup=False)

            with Vertical(id="todo-form-view", classes="todo-view"):
                yield Label("Add todo", id="todo-form-title", classes="todo-title")
                yield TodoTitleInput(placeholder="Title", id="todo-title-input")
                yield TextArea(placeholder="Notes (optional)", id="todo-notes-input")
                yield Input(
                    placeholder="Due date: YYYY-MM-DD (optional)",
                    id="todo-due-date-input",
                )
                yield Static(id="todo-form-error", classes="todo-error", markup=False)
                with HorizontalGroup(classes="todo-form-actions"):
                    yield Button("Save", id="todo-save", variant="success")
                    yield Button("Cancel", id="todo-form-cancel")

            with Vertical(id="todo-detail-view", classes="todo-view"):
                yield Label("Todo", classes="todo-title")
                with VerticalScroll(classes="todo-list"):
                    yield Static(id="todo-detail-content", markup=False)
                with Vertical(classes="todo-actions"):
                    yield Button("Back", id="todo-detail-back")

            with Vertical(id="todo-delete-view", classes="todo-view"):
                yield Label("Delete todo", classes="todo-title")
                yield Static(
                    "This permanently deletes the selected todo.",
                    classes="todo-warning",
                    markup=False,
                )
                with Vertical(classes="todo-actions"):
                    yield Button("Cancel", id="todo-delete-cancel")
                    yield Button(
                        "Delete permanently", id="todo-delete", variant="error"
                    )

            with Vertical(id="todo-clear-view", classes="todo-view"):
                yield Label("Delete todo database", classes="todo-title")
                yield Static(
                    "This permanently deletes every todo and cannot be undone.",
                    classes="todo-warning",
                    markup=False,
                )
                with Vertical(classes="todo-actions"):
                    yield Button("Cancel", id="todo-clear-cancel")
                    yield Button("Delete database", id="todo-clear", variant="error")
        yield Label("Todo", classes="caption")

    def on_mount(self) -> None:
        """Render the persisted summary when the widget first mounts."""
        self.refresh_summary()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id is None:
            return
        actions = {
            "todo-manage": lambda: self.show_view("todo-menu-view"),
            "todo-save": self.save_todo,
            "todo-form-cancel": lambda: self.show_view("todo-menu-view"),
            "todo-detail-back": lambda: self.open_selector("browse"),
            "todo-delete-cancel": lambda: self.open_selector("delete"),
            "todo-clear-cancel": lambda: self.show_view("todo-menu-view"),
        }
        if button_id == "todo-delete":
            self.store.delete_todo(self.selected_todo_id or 0)
            self.refresh_summary()
            self.show_view("todo-menu-view")
        elif button_id == "todo-clear":
            self.store.delete_database()
            self.refresh_summary()
            self.close_context()
        elif action := actions.get(button_id):
            action()

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        option_id = event.option_id
        if option_id is None:
            return
        if event.option_list.id == "todo-menu-list":
            if option_id == "exit":
                self.close_context()
            else:
                self.pending_action = option_id
                self.continue_action()
        elif event.option_list.id == "todo-selector-list":
            if option_id == "back":
                self.show_view("todo-menu-view")
            elif option_id.startswith("todo-"):
                self.select_todo(int(option_id.removeprefix("todo-")))

    def continue_action(self) -> None:
        """Open the view associated with the pending context-menu action."""
        if self.pending_action == "add":
            self.open_form()
        elif self.pending_action in {"browse", "edit", "delete"}:
            self.open_selector(self.pending_action)
        elif self.pending_action == "clear":
            self.show_view("todo-clear-view")

    def open_selector(self, mode: str) -> None:
        """Show todos in insertion order for browsing, editing, or deletion."""
        title = self.query_one("#todo-selector-title", Label)
        title.update(f"{mode.title()} todo")
        options = [
            Option(self.todo_option_label(todo), id=f"todo-{todo.id}")
            for todo in self.store.list_todos()
        ]
        if not options:
            options = [Option("No todos available", id="empty", disabled=True)]
        options.append(Option("Back", id="back"))
        self.query_one("#todo-selector-list", TodoOptionList).set_options(options)
        self.show_view("todo-selector-view")

    def select_todo(self, todo_id: int) -> None:
        """Open the selected todo in the view required by the current mode."""
        todo = self.store.get_todo(todo_id)
        if todo is None:
            self.open_selector(self.pending_action or "browse")
            return
        self.selected_todo_id = todo.id
        if self.pending_action == "edit":
            self.open_form(todo)
        elif self.pending_action == "delete":
            self.show_view("todo-delete-view")
        else:
            self.show_detail(todo)

    def open_form(self, todo: TodoItem | None = None) -> None:
        """Open the shared form for a new or existing todo."""
        self.selected_todo_id = todo.id if todo else None
        title_label = self.query_one("#todo-form-title", Label)
        title_label.update("Edit todo" if todo else "Add todo")
        self.query_one("#todo-title-input", Input).value = todo.title if todo else ""
        self.query_one("#todo-notes-input", TextArea).text = (
            todo.notes or "" if todo else ""
        )
        self.query_one("#todo-due-date-input", Input).value = (
            todo.due_date or "" if todo else ""
        )
        self.query_one("#todo-form-error", Static).update("")
        self.show_view("todo-form-view")

    def save_todo(self) -> None:
        """Validate and persist values from the add/edit form."""
        title = self.query_one("#todo-title-input", Input).value.strip()
        notes = self.query_one("#todo-notes-input", TextArea).text.strip() or None
        due_date = self.query_one("#todo-due-date-input", Input).value.strip() or None
        error = self.query_one("#todo-form-error", Static)
        if not title:
            error.update("Title is required.")
            return
        if due_date is not None:
            try:
                date.fromisoformat(due_date)
            except ValueError:
                error.update("Due date must use YYYY-MM-DD.")
                return
        if self.selected_todo_id is None:
            self.store.create_todo(title, notes, due_date)
        else:
            self.store.update_todo(self.selected_todo_id, title, notes, due_date)
        self.refresh_summary()
        self.show_view("todo-menu-view")

    def show_detail(self, todo: TodoItem) -> None:
        """Display all fields for a selected todo."""
        content = self.query_one("#todo-detail-content", Static)
        content.update(
            f"{todo.title}\n\nDue: {todo.due_date or 'No due date'}\n\n"
            f"{todo.notes or 'No notes'}"
        )
        self.show_view("todo-detail-view")

    def refresh_summary(self) -> None:
        """Refresh the non-interactive, scrollable todo summary."""
        summary = self.query_one("#todo-summary-list", Static)
        if not self.store.exists():
            summary.update("No todo database yet.\n\nSelect Manage todos to begin.")
            return
        todos = self.store.list_todos()
        if not todos:
            summary.update("No todos yet.")
            return
        visible = todos[: self.max_items]
        lines = [self.todo_option_label(todo) for todo in visible]
        hidden = len(todos) - len(visible)
        if hidden:
            lines.append(f"... and {hidden} more")
        summary.update("\n".join(lines))

    def show_view(self, view_id: str) -> None:
        """Switch views and indicate whether keyboard input is captured."""
        views = self.query_one("#todo-views", ContentSwitcher)
        views.current = view_id
        views.get_child_by_id(view_id).display = True
        self.set_class(view_id != "todo-summary", "interacting")

    def close_context(self) -> None:
        """Clear interaction state and return to the summary."""
        self.pending_action = None
        self.selected_todo_id = None
        self.refresh_summary()
        self.show_view("todo-summary")

    def action_back(self) -> None:
        """Move towards the summary when Escape is pressed."""
        views = self.query_one("#todo-views", ContentSwitcher)
        if views.current == "todo-summary":
            return
        if views.current == "todo-menu-view":
            self.close_context()
        else:
            self.show_view("todo-menu-view")

    @staticmethod
    def todo_option_label(todo: TodoItem) -> str:
        """Format a todo for the summary and selector views."""
        due = f" — due {todo.due_date}" if todo.due_date else ""
        return f"{todo.id}. {todo.title}{due}"
