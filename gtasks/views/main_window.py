from concurrent.futures import Future, ThreadPoolExecutor

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib, Gtk, Pango

from gtasks.controllers.task_controller import TaskController
from gtasks.models.task import Task
from gtasks.models.task_list import TaskList


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application, controller: TaskController) -> None:
        super().__init__(application=application, title="GTasks")
        self._controller = controller
        self._rows: dict[Gtk.ListBoxRow, tuple[str, str]] = {}
        self._groups: dict[str, Gtk.ListBox] = {}
        self._refreshing = False
        self._closed = False
        self._task_generation = 0
        self._last_tasks: list[Task] = []
        self._accounts_generation = 0
        self._executor = ThreadPoolExecutor(max_workers=3)
        self.set_default_size(900, 560)
        self.connect("close-request", self._on_close)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        refresh_button = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_button.set_tooltip_text("Atualizar listas e tarefas")
        refresh_button.connect("clicked", self._refresh_google)
        header.pack_end(refresh_button)
        toolbar.add_top_bar(header)

        layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        layout.append(self._create_sidebar())
        layout.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        layout.append(self._create_content())
        toolbar.set_content(layout)
        self.set_content(toolbar)

        self._refresh_lists()
        self._refresh_google()

    def _on_close(self, _window) -> bool:
        self._closed = True
        self._executor.shutdown(wait=False, cancel_futures=True)
        return False

    def _submit(self, action, callback, message: str, on_error=None) -> None:
        if self._closed:
            return
        self._status.set_label(message)
        future = self._executor.submit(action)
        future.add_done_callback(
            lambda completed: GLib.idle_add(self._finish, completed, callback, on_error)
        )

    def _finish(self, future: Future, callback, on_error) -> bool:
        if self._closed:
            return GLib.SOURCE_REMOVE
        try:
            result = future.result()
        except Exception as error:
            if on_error is not None:
                on_error()
            # Never display raw network responses or authorization credentials.
            if isinstance(error, (ValueError, RuntimeError, KeyError)):
                self._status.set_label(str(error))
            else:
                self._status.set_label("Falha ao acessar o Google Tasks.")
        else:
            self._status.set_label("")
            callback(result)
        return GLib.SOURCE_REMOVE

    def _create_sidebar(self) -> Gtk.Widget:
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        sidebar.set_size_request(250, -1)
        sidebar.set_margin_top(18)
        sidebar.set_margin_start(12)
        sidebar.set_margin_end(12)
        sidebar.set_margin_bottom(12)

        local_group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        local_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        local_name = Gtk.Label(label="Neste dispositivo", xalign=0, hexpand=True)
        local_name.add_css_class("heading")
        local_header.append(local_name)

        local_add = Gtk.Button(icon_name="list-add-symbolic")
        local_add.add_css_class("flat")
        local_add.set_tooltip_text("Criar lista local")
        local_add.connect("clicked", self._show_create_list_dialog, "local")
        local_header.append(local_add)
        local_group.append(local_header)

        local_box = Gtk.ListBox()
        local_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        local_box.add_css_class("navigation-sidebar")
        local_box.connect("row-selected", self._on_list_selected)
        self._groups["local"] = local_box
        local_group.append(local_box)
        sidebar.append(local_group)

        self._google_group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        google_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        google_header.append(Gtk.Image.new_from_icon_name("network-server-symbolic"))
        google_name = Gtk.Label(label="Google Tasks", xalign=0, hexpand=True)
        google_name.add_css_class("heading")
        google_header.append(google_name)
        self._google_group.append(google_header)

        self._google_accounts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._google_group.append(self._google_accounts)
        sidebar.append(self._google_group)

        self._status = Gtk.Label(label="", xalign=0, wrap=True)
        self._status.add_css_class("dim-label")
        sidebar.append(self._status)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(sidebar)
        return scroll

    def _build_account_groups(self) -> None:
        self._refreshing = True
        for source in list(self._groups):
            if source != "local":
                del self._groups[source]
        while child := self._google_accounts.get_first_child():
            self._google_accounts.remove(child)

        accounts = self._controller.remote_accounts()
        if not accounts:
            hint = Gtk.Label(
                label="Adicione uma conta Google em Configurações → Contas Online.",
                xalign=0,
                wrap=True,
            )
            hint.add_css_class("dim-label")
            self._google_accounts.append(hint)

        for source, identity in accounts:
            group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

            account_label = Gtk.Label(label=identity, xalign=0, hexpand=True)
            account_label.set_ellipsize(Pango.EllipsizeMode.END)
            account_label.add_css_class("dim-label")
            account_label.set_tooltip_text(identity)
            header.append(account_label)

            add = Gtk.Button(icon_name="list-add-symbolic")
            add.add_css_class("flat")
            add.set_tooltip_text("Criar lista no Google Tasks")
            add.connect("clicked", self._show_create_list_dialog, source)
            header.append(add)
            group.append(header)

            list_box = Gtk.ListBox()
            list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
            list_box.add_css_class("navigation-sidebar")
            list_box.connect("row-selected", self._on_list_selected)
            self._groups[source] = list_box
            group.append(list_box)
            self._google_accounts.append(group)
        self._refreshing = False

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

    def _refresh_google(self, _button=None) -> None:
        self._accounts_generation += 1
        generation = self._accounts_generation

        def found(sources) -> None:
            if generation != self._accounts_generation:
                return
            self._controller.register_remote(sources)
            self._build_account_groups()
            self._refresh_lists()
            for source, _identity in self._controller.remote_accounts():
                self._load_remote_lists(source)

        self._submit(self._controller.discover_remote, found, "Procurando contas Google...")

    def _load_remote_lists(self, source: str) -> None:
        def loaded(lists) -> None:
            if not self._controller.has_source(source):
                return
            self._controller.cache_remote_lists(source, lists)
            self._refresh_lists()

        self._submit(
            lambda: self._controller.load_remote_lists(source),
            loaded,
            "Atualizando listas do Google...",
        )

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
        name = entry.get_text()
        if source == "local":
            self._controller.create_list(name)
            self._refresh_lists()
            return

        def created(task_list: TaskList) -> None:
            self._controller.cache_created_remote_list(task_list)
            self._refresh_lists()

        self._submit(
            lambda: self._controller.create_list(name, source),
            created,
            "Criando lista no Google...",
        )

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
        selected = self._controller.selected_list
        title = self._task_entry.get_text().strip()
        if not title or selected is None:
            return
        if selected.source == "local":
            self._controller.create_task_for(selected, title)
            self._task_entry.set_text("")
            self._refresh_tasks()
            return

        self._task_entry.set_sensitive(False)
        self._add_task_button.set_sensitive(False)

        def created(_task: Task) -> None:
            if self._controller.selected_list == selected:
                self._task_entry.set_text("")
                self._refresh_tasks()

        def failed() -> None:
            self._task_entry.set_sensitive(True)
            self._add_task_button.set_sensitive(True)

        self._submit(
            lambda: self._controller.create_task_for(selected, title),
            created,
            "Salvando tarefa no Google...",
            on_error=failed,
        )

    def _on_task_toggled(self, check: Gtk.CheckButton, task_id: str) -> None:
        selected = self._controller.selected_list
        if selected is None:
            return
        if selected.source == "local":
            self._controller.set_completed_for(selected, task_id, check.get_active())
            return

        completed = check.get_active()
        check.set_sensitive(False)

        def failed() -> None:
            if self._controller.selected_list == selected:
                self._render_tasks(self._last_tasks)

        self._submit(
            lambda: self._controller.set_completed_for(selected, task_id, completed),
            lambda _task: self._refresh_tasks(),
            "Atualizando tarefa no Google...",
            on_error=failed,
        )

    def _refresh_tasks(self) -> None:
        self._task_generation += 1
        self._last_tasks = []
        generation = self._task_generation
        selected = self._controller.selected_list
        self._title.set_label(selected.name if selected else "Selecione uma lista")
        self._source_label.set_label(
            ("Salvo neste dispositivo" if selected.source == "local" else "Google Tasks")
            if selected else ""
        )
        self._task_entry.set_sensitive(selected is not None)
        self._add_task_button.set_sensitive(selected is not None)

        while row := self._tasks_box.get_row_at_index(0):
            self._tasks_box.remove(row)

        if selected is None:
            self._empty_label.set_label("Crie uma lista para começar")
            return
        if selected.source == "local":
            self._render_tasks(self._controller.get_tasks_for(selected))
            return

        self._empty_label.set_label("Carregando tarefas do Google...")

        def loaded(tasks: list[Task]) -> None:
            if generation != self._task_generation:
                return
            if self._controller.selected_list != selected:
                return
            self._render_tasks(tasks)

        self._submit(
            lambda: self._controller.get_tasks_for(selected),
            loaded,
            "Sincronizando tarefas...",
        )

    def _render_tasks(self, tasks: list[Task]) -> None:
        self._last_tasks = list(tasks)
        self._empty_label.set_label("Esta lista não tem tarefas")
        while row := self._tasks_box.get_row_at_index(0):
            self._tasks_box.remove(row)

        for task in tasks:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_margin_top(10)
            box.set_margin_bottom(10)
            box.set_margin_start(12)
            box.set_margin_end(12)

            check = Gtk.CheckButton(active=task.completed)
            # Pass the desired status from the UI thread, not the worker thread.
            check.connect("toggled", self._on_task_toggled, task.id)
            box.append(check)

            title = Gtk.Label(label=task.title, xalign=0, hexpand=True, wrap=True)
            if task.completed:
                title.add_css_class("dim-label")
            box.append(title)
            row.set_child(box)
            self._tasks_box.append(row)
