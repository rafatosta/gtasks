from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from gtasks.models.task import Task
from gtasks.models.task_list import TaskList


class TaskPanel(Gtk.Box):
    """Displays the selected list and emits user actions."""

    def __init__(
        self,
        on_add_task: Callable[[str], None],
        on_toggle_task: Callable[[str, bool], None],
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self._on_add_task = on_add_task
        self._on_toggle_task = on_toggle_task
        self._tasks: list[Task] = []
        self.set_hexpand(True)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)

        self._title = Gtk.Label(label="Selecione uma lista", xalign=0)
        self._title.add_css_class("title-1")
        self.append(self._title)

        self._source_label = Gtk.Label(xalign=0)
        self._source_label.add_css_class("dim-label")
        self.append(self._source_label)

        add_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._entry = Gtk.Entry(
            placeholder_text="Adicionar uma tarefa", hexpand=True
        )
        self._entry.connect("activate", self._submit_task)
        add_row.append(self._entry)

        self._add_button = Gtk.Button(icon_name="list-add-symbolic")
        self._add_button.set_tooltip_text("Adicionar tarefa")
        self._add_button.connect("clicked", self._submit_task)
        add_row.append(self._add_button)
        self.append(add_row)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._list_box.add_css_class("boxed-list")
        self._empty_label = Gtk.Label(label="Crie uma lista para começar")
        self._empty_label.add_css_class("dim-label")
        self._empty_label.set_margin_top(40)
        self._list_box.set_placeholder(self._empty_label)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(self._list_box)
        self.append(scroll)
        self.set_input_enabled(False)

    def set_list(self, task_list: TaskList | None) -> None:
        self._title.set_label(task_list.name if task_list else "Selecione uma lista")
        source = ""
        if task_list is not None:
            source = (
                "Salvo neste dispositivo"
                if task_list.source == "local"
                else "Google Tasks"
            )
        self._source_label.set_label(source)
        self.set_input_enabled(task_list is not None)

    def set_input_enabled(self, enabled: bool) -> None:
        self._entry.set_sensitive(enabled)
        self._add_button.set_sensitive(enabled)

    def clear_entry(self) -> None:
        self._entry.set_text("")

    def show_message(self, message: str) -> None:
        self._tasks = []
        self._clear_rows()
        self._empty_label.set_label(message)

    def show_tasks(self, tasks: list[Task]) -> None:
        self._tasks = list(tasks)
        self._clear_rows()
        self._empty_label.set_label("Esta lista não tem tarefas")
        for task in tasks:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_margin_top(10)
            box.set_margin_bottom(10)
            box.set_margin_start(12)
            box.set_margin_end(12)

            check = Gtk.CheckButton(active=task.completed)
            check.connect("toggled", self._task_toggled, task.id)
            box.append(check)

            title = Gtk.Label(label=task.title, xalign=0, hexpand=True, wrap=True)
            if task.completed:
                title.add_css_class("dim-label")
            box.append(title)
            row.set_child(box)
            self._list_box.append(row)

    def restore_tasks(self) -> None:
        self.show_tasks(self._tasks)

    def _clear_rows(self) -> None:
        while row := self._list_box.get_row_at_index(0):
            self._list_box.remove(row)

    def _submit_task(self, _widget: Gtk.Widget) -> None:
        title = self._entry.get_text().strip()
        if title:
            self._on_add_task(title)

    def _task_toggled(self, check: Gtk.CheckButton, task_id: str) -> None:
        check.set_sensitive(False)
        self._on_toggle_task(task_id, check.get_active())
