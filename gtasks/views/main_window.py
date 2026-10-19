import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

from gtasks.controllers.task_controller import TaskController
from gtasks.models.task import Task
from gtasks.views.list_sidebar import ListSidebar
from gtasks.views.task_panel import TaskPanel


class MainWindow(Adw.ApplicationWindow):
    """Composes the sidebar and task panel, connecting them to the controller."""

    def __init__(self, application: Adw.Application, controller: TaskController) -> None:
        super().__init__(application=application, title="GTasks")
        self._controller = controller
        self._closed = False
        self._task_generation = 0
        self._accounts_generation = 0
        self.set_default_size(900, 560)
        self.connect("close-request", self._on_close)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        refresh_button = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_button.set_tooltip_text("Atualizar listas e tarefas")
        refresh_button.connect("clicked", self._refresh_google)
        header.pack_end(refresh_button)
        toolbar.add_top_bar(header)

        self._sidebar = ListSidebar(
            on_create_list=self._show_create_list_dialog,
            on_select_list=self._select_list,
        )
        self._task_panel = TaskPanel(
            on_add_task=self._add_task,
            on_toggle_task=self._toggle_task,
        )

        layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        layout.append(self._sidebar)
        layout.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        layout.append(self._task_panel)
        toolbar.set_content(layout)
        self.set_content(toolbar)

        self._refresh_lists()
        self._refresh_google()

    def _on_close(self, _window: Adw.ApplicationWindow) -> bool:
        self._closed = True
        self._controller.close()
        return False

    def _request(self, submit, callback, message: str, on_error=None) -> None:
        if self._closed:
            return
        self._sidebar.set_status(message)

        def succeeded(result) -> None:
            if not self._closed:
                self._sidebar.set_status("")
                callback(result)

        def failed(error: Exception) -> None:
            if self._closed:
                return
            if on_error is not None:
                on_error()
            if isinstance(error, (ValueError, RuntimeError, KeyError)):
                self._sidebar.set_status(str(error))
            else:
                self._sidebar.set_status("Não foi possível concluir a operação.")

        submit(succeeded, failed)

    def _refresh_google(self, _button: Gtk.Button | None = None) -> None:
        self._accounts_generation += 1
        generation = self._accounts_generation

        def found(accounts: list[tuple[str, str]]) -> None:
            if generation != self._accounts_generation:
                return
            self._sidebar.set_accounts(accounts)
            self._refresh_lists()
            for source, _identity in accounts:
                self._load_remote_lists(source)

        self._request(
            self._controller.discover_remote_async,
            found,
            "Procurando contas Google...",
        )

    def _load_remote_lists(self, source: str) -> None:
        self._request(
            lambda success, error: self._controller.load_remote_lists_async(
                source, success, error
            ),
            lambda _lists: self._refresh_lists(),
            "Atualizando listas do Google...",
        )

    def _show_create_list_dialog(self, source: str) -> None:
        dialog = Adw.AlertDialog.new("Nova lista", "Escolha um nome para a lista.")
        entry = Gtk.Entry(text="Nova lista")
        entry.select_region(0, -1)
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("create", "Criar")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("create")
        dialog.connect("response", self._create_list, entry, source)
        dialog.present(self)

    def _create_list(
        self, _dialog: Adw.AlertDialog, response: str, entry: Gtk.Entry, source: str
    ) -> None:
        if response != "create" or not entry.get_text().strip():
            return
        name = entry.get_text()
        self._request(
            lambda success, error: self._controller.create_list_async(
                name, source, success, error
            ),
            lambda _created: self._refresh_lists(),
            "Criando lista...",
        )

    def _select_list(self, source: str, list_id: str) -> None:
        self._controller.select_list(list_id, source)
        self._refresh_tasks()

    def _refresh_lists(self) -> None:
        self._sidebar.set_lists(
            self._controller.get_lists(),
            self._controller.selected_list,
        )
        self._refresh_tasks()

    def _add_task(self, title: str) -> None:
        selected = self._controller.selected_list
        if selected is None:
            return
        self._task_panel.set_input_enabled(False)

        def created(_task: Task) -> None:
            if self._controller.selected_list == selected:
                self._task_panel.clear_entry()
                self._refresh_tasks()

        def failed() -> None:
            self._task_panel.set_input_enabled(
                self._controller.selected_list is not None
            )

        self._request(
            lambda success, error: self._controller.create_task_async(
                selected, title, success, error
            ),
            created,
            "Salvando tarefa...",
            on_error=failed,
        )

    def _toggle_task(self, task_id: str, completed: bool) -> None:
        selected = self._controller.selected_list
        if selected is None:
            return

        def failed() -> None:
            if self._controller.selected_list == selected:
                self._task_panel.restore_tasks()

        self._request(
            lambda success, error: self._controller.set_completed_async(
                selected, task_id, completed, success, error
            ),
            lambda _task: self._refresh_tasks(),
            "Atualizando tarefa...",
            on_error=failed,
        )

    def _refresh_tasks(self) -> None:
        self._task_generation += 1
        generation = self._task_generation
        selected = self._controller.selected_list
        self._task_panel.set_list(selected)

        if selected is None:
            self._task_panel.show_message("Crie uma lista para começar")
            return
        self._task_panel.show_message("Carregando tarefas...")

        def loaded(tasks: list[Task]) -> None:
            if generation != self._task_generation:
                return
            if self._controller.selected_list == selected:
                self._task_panel.show_tasks(tasks)

        def failed() -> None:
            if generation == self._task_generation:
                self._task_panel.show_message(
                    "Não foi possível carregar as tarefas. Tente atualizar."
                )

        self._request(
            lambda success, error: self._controller.get_tasks_async(
                selected, success, error
            ),
            loaded,
            "Carregando tarefas...",
            on_error=failed,
        )
