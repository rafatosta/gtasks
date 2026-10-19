import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

from gtasks.controllers.task_controller import TaskController


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application, controller: TaskController) -> None:
        super().__init__(application=application, title="GTasks")
        self._controller = controller
        self._rows: dict[Gtk.ListBoxRow, tuple[str, str]] = {}
        self._groups: dict[str, Gtk.ListBox] = {}
        self._refreshing = False
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
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        sidebar.set_size_request(240, -1)
        sidebar.set_margin_top(18)
        sidebar.set_margin_start(12)
        sidebar.set_margin_end(12)
        sidebar.set_margin_bottom(12)

        for source, label in (
            ("local", "Neste dispositivo"),
            ("google", "Google Tasks"),
        ):
            group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            if source == "google":
                header.append(Gtk.Image.new_from_icon_name("network-server-symbolic"))
            name = Gtk.Label(label=label, xalign=0, hexpand=True)
            name.add_css_class("heading")
            header.append(name)

            add_button = Gtk.Button(icon_name="list-add-symbolic")
            add_button.add_css_class("flat")
            add_button.set_tooltip_text(
                "Criar lista local" if source == "local" else "Criar lista no Google Tasks"
            )
            add_button.set_sensitive(self._controller.has_source(source))
            add_button.connect("clicked", self._show_create_list_dialog, source)
            header.append(add_button)
            group.append(header)

            list_box = Gtk.ListBox()
            list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
            list_box.add_css_class("navigation-sidebar")
            list_box.connect("row-selected", self._on_list_selected)
            self._groups[source] = list_box
            group.append(list_box)

            if not self._controller.has_source(source):
                hint = Gtk.Label(label="Sincronização ainda não disponível", xalign=0)
                hint.add_css_class("dim-label")
                hint.set_wrap(True)
                group.append(hint)

            sidebar.append(group)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(sidebar)
        return scroll

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

        self._source_label = Gtk.Label(xalign=0)
        self._source_label.add_css_class("dim-label")
        content.append(self._source_label)

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

    def _show_create_list_dialog(self, _button: Gtk.Button, source: str) -> None:
        dialog = Adw.AlertDialog.new("Nova lista", "Escolha um nome para a lista.")
        name_entry = Gtk.Entry(text="Nova lista")
        name_entry.select_region(0, -1)
        dialog.set_extra_child(name_entry)
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("create", "Criar")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("create")
        dialog.connect("response", self._on_create_list_response, name_entry, source)
        dialog.present(self)

    def _on_create_list_response(
        self, _dialog: Adw.AlertDialog, response: str, entry: Gtk.Entry, source: str
    ) -> None:
        if response != "create" or not entry.get_text().strip():
            return
        self._controller.create_list(entry.get_text(), source)
        self._refresh_lists()

    def _on_list_selected(self, _box: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        if self._refreshing or row is None:
            return

        source, list_id = self._rows[row]
        self._controller.select_list(list_id, source)
        self._refreshing = True
        for other_source, box in self._groups.items():
            if other_source != source:
                box.unselect_all()
        self._refreshing = False
        self._refresh_tasks()

    def _refresh_lists(self) -> None:
        self._refreshing = True
        self._rows.clear()
        for box in self._groups.values():
            while row := box.get_row_at_index(0):
                box.remove(row)

        selected_row = None
        for task_list in self._controller.get_lists():
            box = self._groups.get(task_list.source)
            if box is None:
                continue
            row = Gtk.ListBoxRow()
            name = Gtk.Label(label=task_list.name, xalign=0)
            name.set_margin_top(10)
            name.set_margin_bottom(10)
            name.set_margin_start(12)
            name.set_margin_end(12)
            row.set_child(name)
            self._rows[row] = (task_list.source, task_list.id)
            box.append(row)
            if self._controller.selected_list == task_list:
                selected_row = (box, row)

        if selected_row is not None:
            selected_row[0].select_row(selected_row[1])

        self._refreshing = False
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
        self._source_label.set_label(
            ("Salvo neste dispositivo" if selected.source == "local" else "Google Tasks")
            if selected else ""
        )
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
