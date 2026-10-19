import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

from gtasks.controllers.task_controller import TaskController


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application, controller: TaskController) -> None:
        super().__init__(application=application, title="GTasks")
        self._controller = controller
        self._rows: dict[Gtk.ListBoxRow, str] = {}
        self.set_default_size(860, 540)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())

        layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        layout.append(self._create_sidebar())
        layout.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        layout.append(self._create_content())
        toolbar.set_content(layout)
        self.set_content(toolbar)

        self._refresh_lists()

    def _create_sidebar(self) -> Gtk.Widget:
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        sidebar.set_size_request(230, -1)
        sidebar.set_margin_top(18)
        sidebar.set_margin_start(12)
        sidebar.set_margin_end(12)
        sidebar.set_margin_bottom(12)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        label = Gtk.Label(label="Listas", xalign=0, hexpand=True)
        label.add_css_class("heading")
        header.append(label)

        add_button = Gtk.Button(icon_name="list-add-symbolic")
        add_button.set_tooltip_text("Criar lista")
        add_button.connect("clicked", self._show_create_list_dialog)
        header.append(add_button)
        sidebar.append(header)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._list_box.add_css_class("navigation-sidebar")
        self._list_box.connect("row-selected", self._on_list_selected)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(self._list_box)
        sidebar.append(scroll)
        return sidebar

    def _create_content(self) -> Gtk.Widget:
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_hexpand(True)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(24)
        content.set_margin_end(24)

        self._title = Gtk.Label(label="Selecione uma lista", xalign=0)
        self._title.add_css_class("title-1")
        content.append(self._title)

        add_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._task_entry = Gtk.Entry(placeholder_text="Adicionar uma tarefa", hexpand=True)
        self._task_entry.connect("activate", self._add_task)
        add_row.append(self._task_entry)

        self._add_task_button = Gtk.Button(icon_name="list-add-symbolic")
        self._add_task_button.set_tooltip_text("Adicionar tarefa")
        self._add_task_button.connect("clicked", self._add_task)
        add_row.append(self._add_task_button)
        content.append(add_row)

        self._tasks_box = Gtk.ListBox()
        self._tasks_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._tasks_box.add_css_class("boxed-list")
        self._empty_label = Gtk.Label(label="Crie uma lista para começar")
        self._empty_label.add_css_class("dim-label")
        self._empty_label.set_margin_top(40)
        self._tasks_box.set_placeholder(self._empty_label)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(self._tasks_box)
        content.append(scroll)
        return content

    def _show_create_list_dialog(self, _button: Gtk.Button) -> None:
        dialog = Adw.AlertDialog.new("Nova lista", "Escolha um nome para a lista.")
        name_entry = Gtk.Entry(text="Nova lista")
        name_entry.select_region(0, -1)
        dialog.set_extra_child(name_entry)
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("create", "Criar")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("create")
        dialog.connect("response", self._on_create_list_response, name_entry)
        dialog.present(self)

    def _on_create_list_response(
        self, _dialog: Adw.AlertDialog, response: str, entry: Gtk.Entry
    ) -> None:
        if response != "create" or not entry.get_text().strip():
            return
        self._controller.create_list(entry.get_text())
        self._refresh_lists()

    def _on_list_selected(self, _box: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        if row is None:
            return
        self._controller.select_list(self._rows[row])
        self._refresh_tasks()

    def _refresh_lists(self) -> None:
        self._rows.clear()
        while row := self._list_box.get_row_at_index(0):
            self._list_box.remove(row)

        selected_row = None
        for task_list in self._controller.get_lists():
            row = Gtk.ListBoxRow()
            name = Gtk.Label(label=task_list.name, xalign=0)
            name.set_margin_top(10)
            name.set_margin_bottom(10)
            name.set_margin_start(12)
            name.set_margin_end(12)
            row.set_child(name)
            self._rows[row] = task_list.id
            self._list_box.append(row)
            if self._controller.selected_list == task_list:
                selected_row = row

        if selected_row is not None:
            self._list_box.select_row(selected_row)
        else:
            self._refresh_tasks()

    def _add_task(self, _widget: Gtk.Widget) -> None:
        title = self._task_entry.get_text().strip()
        if not title or self._controller.selected_list is None:
            return
        self._controller.create_task(title)
        self._task_entry.set_text("")
        self._refresh_tasks()

    def _on_task_toggled(self, check: Gtk.CheckButton, task_id: str) -> None:
        self._controller.set_completed(task_id, check.get_active())

    def _refresh_tasks(self) -> None:
        selected = self._controller.selected_list
        self._title.set_label(selected.name if selected else "Selecione uma lista")
        self._task_entry.set_sensitive(selected is not None)
        self._add_task_button.set_sensitive(selected is not None)
        self._empty_label.set_label(
            "Esta lista não tem tarefas" if selected else "Crie uma lista para começar"
        )

        while row := self._tasks_box.get_row_at_index(0):
            self._tasks_box.remove(row)

        for task in self._controller.get_tasks():
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_margin_top(10)
            box.set_margin_bottom(10)
            box.set_margin_start(12)
            box.set_margin_end(12)

            check = Gtk.CheckButton(active=task.completed)
            check.connect("toggled", self._on_task_toggled, task.id)
            box.append(check)

            title = Gtk.Label(label=task.title, xalign=0, hexpand=True, wrap=True)
            if task.completed:
                title.add_css_class("dim-label")
            box.append(title)
            row.set_child(box)
            self._tasks_box.append(row)
