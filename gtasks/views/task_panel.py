from collections.abc import Callable
from datetime import date

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib, Gtk, Pango

from gtasks.models.task import Task
from gtasks.models.task_list import TaskList


class TaskPanel(Gtk.Box):
    """Displays the selected list and emits user actions."""

    def __init__(
        self,
        on_add_task: Callable[[str], None],
        on_toggle_task: Callable[[str, bool], None],
        on_task_action: Callable[[Task, str], None] | None = None,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self._on_task_action = on_task_action
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
        # Keep cached children next to their parent without relying on fetch order.
        children: dict[str | None, list[Task]] = {}
        by_id = {task.id: task for task in tasks}
        for task in tasks:
            children.setdefault(task.parent if task.parent in by_id else None, []).append(task)
        pending = [(task, 0) for task in reversed(children.get(None, []))]
        visited = set()
        ordered = []
        while pending:
            task, depth = pending.pop()
            if task.id in visited:
                continue
            visited.add(task.id)
            ordered.append((task, depth))
            pending.extend((child, depth + 1) for child in reversed(children.get(task.id, [])))
        ordered.extend((task, 0) for task in tasks if task.id not in visited)
        for task, depth in ordered:
            row = Adw.ActionRow(use_markup=False, title_lines=0)
            row.set_title(task.title)
            subtitle = []
            if task.parent:
                parent = by_id.get(task.parent)
                subtitle.append("Subtarefa" + (f" de {parent.title}" if parent else ""))
            if task.due:
                subtitle.append("Data: " + date.fromisoformat(task.due).strftime("%d/%m/%Y"))
            if task.notes:
                subtitle.append(task.notes.replace("\n", " "))
            row.set_subtitle(" · ".join(subtitle))
            row.set_subtitle_lines(2)
            check = Gtk.CheckButton(active=task.completed)
            check.set_valign(Gtk.Align.CENTER)
            check.set_tooltip_text("Marcar como pendente" if task.completed else "Concluir tarefa")
            check.update_property([Gtk.AccessibleProperty.LABEL], [task.title])
            check.connect("toggled", self._task_toggled, task.id)
            check.set_margin_start(min(depth, 2) * 12)
            row.add_prefix(check)
            if task.completed:
                row.add_css_class("dim-label")
            if self._on_task_action is not None:
                menu = Gtk.MenuButton(icon_name="view-more-symbolic", valign=Gtk.Align.CENTER)
                menu.add_css_class("flat")
                menu.set_tooltip_text(f"Opções de {task.title}")
                popup = Gtk.Popover()
                actions = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                for label, action in (("Editar detalhes e data", "edit"),
                                      ("Adicionar subtarefa", "subtask"),
                                      ("Mover para outra lista", "move"),
                                      ("Excluir tarefa", "delete")):
                    button = Gtk.Button(label=label)
                    button.add_css_class("flat")
                    if action == "delete":
                        button.add_css_class("destructive-action")
                    if action == "subtask" and (task.assigned or task.parent):
                        button.set_sensitive(False)
                    def activate(_button, item=task, name=action, popover=popup):
                        popover.popdown()
                        self._on_task_action(item, name)
                    button.connect("clicked", activate)
                    actions.append(button)
                popup.set_child(actions)
                menu.set_popover(popup)
                row.add_suffix(menu)
                row.set_activatable(True)
                row.connect("activated", lambda _row, button=menu: button.popup())
                self._connect_row_clicks(row, check, menu, task)
            self._list_box.append(row)

    def _connect_row_clicks(self, row, check, menu, task: Task) -> None:
        # Wait for the desktop double-click interval before opening the popover,
        # otherwise it grabs the pointer before the second click reaches the row.
        pending: int | None = None
        gesture = Gtk.GestureClick(button=1)
        gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)

        def cancel_pending(*_args):
            nonlocal pending
            if pending is not None:
                GLib.source_remove(pending)
                pending = None

        def is_control(x, y):
            target = row.pick(x, y, Gtk.PickFlags.DEFAULT)
            return target is not None and any(
                target == control or target.is_ancestor(control)
                for control in (check, menu)
            )

        def pressed(controller, count, x, y):
            if is_control(x, y):
                cancel_pending()
                return
            controller.set_state(Gtk.EventSequenceState.CLAIMED)
            cancel_pending()

        def released(_controller, count, x, y):
            nonlocal pending
            if is_control(x, y):
                return
            if count == 2:
                menu.popdown()
                self._on_task_action(task, "edit")
            elif count == 1:
                def open_menu():
                    nonlocal pending
                    pending = None
                    if row.get_mapped():
                        menu.popup()
                    return GLib.SOURCE_REMOVE
                interval = row.get_settings().get_property("gtk-double-click-time")
                pending = GLib.timeout_add(interval, open_menu)

        gesture.connect("pressed", pressed)
        gesture.connect("released", released)
        row.add_controller(gesture)
        row.connect("unrealize", cancel_pending)

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
