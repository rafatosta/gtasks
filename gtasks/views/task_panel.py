from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk, Pango

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

        add_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._entry = Gtk.Entry(
            placeholder_text="Adicionar uma tarefa", hexpand=True
        )
        self._entry.set_width_chars(1)
        self._entry.connect("activate", self._submit_task)
        add_row.append(self._entry)

        self._add_button = Gtk.Button(icon_name="list-add-symbolic")
        self._add_button.set_tooltip_text("Adicionar tarefa")
        self._add_button.connect("clicked", self._submit_task)
        add_row.append(self._add_button)
        self.append(add_row)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._list_box.set_valign(Gtk.Align.START)
        self._list_box.add_css_class("boxed-list")
        self._empty_label = Gtk.Label(
            label="Crie uma lista para começar", wrap=True,
            wrap_mode=Pango.WrapMode.WORD_CHAR, justify=Gtk.Justification.CENTER,
        )
        self._empty_label.add_css_class("dim-label")
        self._empty_label.set_margin_top(40)
        self._list_box.set_placeholder(self._empty_label)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(self._list_box)
        self.append(scroll)
        self.set_input_enabled(False)

    def set_list(self, task_list: TaskList | None) -> None:
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

    def show_tasks(
        self, tasks: list[Task], empty_message: str = "Esta lista não tem tarefas"
    ) -> None:
        self._tasks = list(tasks)
        self._clear_rows()
        self._empty_label.set_label(empty_message)
        for task in tasks:
            row = Adw.ActionRow(use_markup=False, title_lines=0)
            row.set_title(task.title)
            check = Gtk.CheckButton(active=task.completed)
            check.set_valign(Gtk.Align.CENTER)
            check.set_tooltip_text("Marcar como pendente" if task.completed else "Concluir tarefa")
            check.update_property([Gtk.AccessibleProperty.LABEL], [task.title])
            check.connect("toggled", self._task_toggled, task.id)
            row.add_prefix(check)
            row.set_activatable_widget(check)
            if task.completed:
                row.add_css_class("dim-label")
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
