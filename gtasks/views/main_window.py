import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk

from gtasks.controllers.task_controller import TaskController
from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.views.list_sidebar import ListSidebar
from gtasks.views.task_panel import TaskPanel
from gtasks.views.task_editor import create_task_editor


class MainWindow(Adw.ApplicationWindow):
    """Composes the sidebar and task panel, connecting them to the controller."""

    def __init__(
        self,
        application: Adw.Application,
        controller: TaskController,
        settings: Gio.Settings,
    ) -> None:
        super().__init__(application=application, title="GTasks")
        self._controller = controller
        self._settings = settings
        self._sync_timer: int | None = None
        self._restore_pending = settings.get_boolean("restore-last-list")
        self._interval_handler = settings.connect(
            "changed::sync-interval", self._on_interval_changed
        )
        self._completed_handler = settings.connect(
            "changed::show-completed", lambda *_: self._refresh_tasks()
        )
        self._closed = False
        self._accounts_generation = 0
        self._auto_sync_run = False
        self.set_default_size(900, 560)
        self.connect("close-request", self._on_close)
        close_action = Gio.SimpleAction.new("close", None)
        close_action.connect("activate", self._close_current)
        self.add_action(close_action)
        refresh_action = Gio.SimpleAction.new("refresh", None)
        refresh_action.connect("activate", lambda *_: self._refresh_google(force=True))
        self.add_action(refresh_action)

        # Breakpoints require an explicit minimum size; support phone-sized widths.
        self.set_size_request(360, 294)
        sidebar_toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()

        main_menu = Gio.Menu()
        main_menu.append("Preferências", "app.preferences")
        main_menu.append("Atalhos de teclado", "app.shortcuts")
        main_menu.append("Sobre o GTasks", "app.about")
        main_menu.append("Sair", "app.quit")
        menu_button = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_button.set_tooltip_text("Menu principal (F10)")
        menu_button.set_primary(True)
        menu_button.set_menu_model(main_menu)
        header.pack_start(menu_button)
        refresh_button = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_button.set_tooltip_text("Atualizar listas e tarefas")
        refresh_button.set_action_name("win.refresh")
        header.pack_end(refresh_button)
        sidebar_toolbar.add_top_bar(header)

        self._sidebar = ListSidebar(
            on_create_list=self._show_create_list_dialog,
            on_select_list=self._select_list,
            on_edit_list=self._show_edit_list_dialog,
            on_delete_list=self._show_delete_list_dialog,
        )
        self._task_panel = TaskPanel(
            on_add_task=self._add_task,
            on_toggle_task=self._toggle_task,
            on_task_action=self._task_action,
        )

        sidebar_toolbar.set_content(self._sidebar)
        sidebar_page = Adw.NavigationPage.new(sidebar_toolbar, "Listas")
        sidebar_page.add_css_class("sidebar")

        content_toolbar = Adw.ToolbarView()
        content_header = Adw.HeaderBar()
        self._content_title = Adw.WindowTitle(title="GTasks")
        content_header.set_title_widget(self._content_title)
        content_toolbar.add_top_bar(content_header)
        clamp = Adw.Clamp(maximum_size=720, tightening_threshold=480)
        clamp.set_child(self._task_panel)
        content_toolbar.set_content(clamp)
        self._content_page = Adw.NavigationPage.new(content_toolbar, "Tarefas")

        self._split_view = Adw.NavigationSplitView(
            min_sidebar_width=260, max_sidebar_width=320,
            sidebar_width_fraction=0.3,
        )
        self._split_view.set_sidebar(sidebar_page)
        self._split_view.set_content(self._content_page)
        breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 660sp"))
        breakpoint.add_setter(self._split_view, "collapsed", True)
        self.add_breakpoint(breakpoint)

        self._toast_overlay = Adw.ToastOverlay()
        self._toast_overlay.set_child(self._split_view)
        self.set_content(self._toast_overlay)

        self._refresh_lists()
        self._refresh_google()
        self._configure_auto_sync()

    def _close_current(self, _action, _parameter) -> None:
        dialog = self.get_visible_dialog()
        if dialog is not None:
            dialog.close()
        else:
            self.close()

    def _on_close(self, _window: Adw.ApplicationWindow) -> bool:
        if self._closed:
            return False
        self._closed = True
        if self._sync_timer is not None:
            GLib.source_remove(self._sync_timer)
            self._sync_timer = None
        self._settings.disconnect(self._interval_handler)
        self._settings.disconnect(self._completed_handler)
        self._controller.close()
        return False

    def _on_interval_changed(self, _settings: Gio.Settings, _key: str) -> None:
        self._configure_auto_sync()

    def _configure_auto_sync(self) -> None:
        if self._sync_timer is not None:
            GLib.source_remove(self._sync_timer)
            self._sync_timer = None
        interval = self._settings.get_int("sync-interval")
        if interval > 0:
            self._sync_timer = GLib.timeout_add_seconds(
                interval * 60, self._periodic_sync
            )

    def _periodic_sync(self) -> bool:
        if self._closed:
            return GLib.SOURCE_REMOVE
        self._auto_sync_run = True
        self._refresh_google()
        return GLib.SOURCE_CONTINUE

    def _try_restore_selection(self) -> None:
        if not self._restore_pending:
            return
        source = self._settings.get_string("last-source")
        list_id = self._settings.get_string("last-list-id")
        if not source or not list_id:
            self._restore_pending = False
            return
        if any(
            item.source == source and item.id == list_id
            for item in self._controller.get_lists()
        ):
            self._controller.select_list(list_id, source)
            self._split_view.set_show_content(True)
            self._restore_pending = False

    def _remember_selection(self) -> None:
        selected = self._controller.selected_list
        if selected is None:
            return
        self._restore_pending = False
        self._settings.set_string("last-source", selected.source)
        self._settings.set_string("last-list-id", selected.id)

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
                self._show_error(str(error))
            else:
                self._show_error("Não foi possível concluir a operação.")

        submit(succeeded, failed)

    def _show_error(self, message: str) -> None:
        self._sidebar.set_status(message)
        self._toast_overlay.add_toast(Adw.Toast.new(message))

    def _refresh_google(
        self, _button: Gtk.Button | None = None, *, force: bool = False
    ) -> None:
        if _button is not None or force:
            self._auto_sync_run = True
        self._accounts_generation += 1
        generation = self._accounts_generation

        def found(accounts: list[tuple[str, str]]) -> None:
            if generation != self._accounts_generation:
                return
            force_sync = self._auto_sync_run
            self._auto_sync_run = False
            self._sidebar.set_accounts(accounts)
            self._refresh_lists()
            if self._settings.get_boolean("sync-on-startup") or force_sync:
                for source, _identity in accounts:
                    self._sync_account(source)

        self._request(
            self._controller.discover_remote_async,
            found,
            "Procurando contas Google...",
        )

    def _sync_account(self, source: str) -> None:
        def progress(updated_list) -> None:
            if updated_list is None:
                # Refresh the index as soon as it arrives; tasks follow in the background.
                self._refresh_lists()
            elif self._controller.selected_list == updated_list:
                self._refresh_tasks()

        def completed() -> None:
            self._sidebar.set_status("")
            selected = self._controller.selected_list
            if selected is not None and selected.source == source:
                self._refresh_tasks()

        def failed(error: Exception) -> None:
            self._show_error(
                str(error) if isinstance(error, RuntimeError)
                else "Não foi possível sincronizar a conta."
            )
            selected = self._controller.selected_list
            if (selected is not None and selected.source == source
                    and self._controller.cached_tasks(selected) is None):
                self._task_panel.show_message("Sem conexão e sem tarefas em cache.")

        self._controller.sync_account_async(source, progress, completed, failed)

    def _show_create_list_dialog(self, source: str) -> None:
        dialog = Adw.AlertDialog.new("Nova lista", "Escolha um nome para a lista.")
        entry = Gtk.Entry(text="Nova lista")
        entry.select_region(0, -1)
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("create", "Criar")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("create")
        dialog.set_close_response("cancel")
        entry.connect("changed", lambda widget: dialog.set_response_enabled(
            "create", bool(widget.get_text().strip())
        ))
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
            lambda _created: self._after_create_list(),
            "Criando lista...",
        )

    def _show_edit_list_dialog(self, task_list: TaskList) -> None:
        dialog = Adw.AlertDialog.new("Editar lista", "Altere o nome da lista.")
        entry = Gtk.Entry(text=task_list.name)
        entry.select_region(0, -1)
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("save", "Salvar")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("save")
        dialog.set_close_response("cancel")
        dialog.set_response_enabled("save", bool(entry.get_text().strip()))
        entry.connect("changed", lambda widget: dialog.set_response_enabled(
            "save", bool(widget.get_text().strip())
        ))

        def responded(_dialog, response):
            if response == "save":
                self._request(
                    lambda success, error: self._controller.rename_list_async(
                        task_list, entry.get_text(), success, error
                    ),
                    lambda _updated: self._refresh_lists(),
                    "Salvando lista...",
                )

        dialog.connect("response", responded)
        dialog.present(self)

    def _show_delete_list_dialog(self, task_list: TaskList) -> None:
        dialog = Adw.AlertDialog.new(
            "Excluir lista?",
            f'A lista “{task_list.name}” e todas as suas tarefas serão excluídas. '
            "Essa ação não pode ser desfeita.",
        )
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("delete", "Excluir")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")

        def deleted(_result):
            if (self._settings.get_string("last-source") == task_list.source
                    and self._settings.get_string("last-list-id") == task_list.id):
                self._settings.set_string("last-source", "")
                self._settings.set_string("last-list-id", "")
                self._restore_pending = False
            self._refresh_lists()

        def responded(_dialog, response):
            if response == "delete":
                self._request(
                    lambda success, error: self._controller.delete_list_async(
                        task_list, success, error
                    ),
                    deleted,
                    "Excluindo lista...",
                )

        dialog.connect("response", responded)
        dialog.present(self)

    def _after_create_list(self) -> None:
        self._remember_selection()
        self._refresh_lists()
        self._split_view.set_show_content(True)

    def _select_list(self, source: str, list_id: str) -> None:
        self._controller.select_list(list_id, source)
        self._remember_selection()
        self._refresh_tasks()
        self._split_view.set_show_content(True)

    def _refresh_lists(self) -> None:
        self._try_restore_selection()
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

    def _task_action(self, task: Task, action: str) -> None:
        selected = self._controller.selected_list
        if selected is None or selected.id != task.list_id:
            return
        if action == "edit":
            def save(title, notes, due, success, error):
                def saved(updated):
                    self._refresh_tasks()
                    success(updated)
                self._controller.update_task_async(
                    selected, task.id, title, notes, due, saved, error
                )
            create_task_editor(task, save, self._settings).present(self)
        elif action == "delete":
            description = f'A tarefa “{task.title}” e suas subtarefas serão excluídas.'
            if task.assigned:
                description += " Isso também exclui a tarefa no documento ou espaço de origem do Google."
            dialog = Adw.AlertDialog.new("Excluir tarefa?", description)
            dialog.add_response("cancel", "Cancelar")
            dialog.add_response("delete", "Excluir")
            dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("cancel")
            dialog.set_close_response("cancel")
            def delete(_dialog, response):
                if response == "delete":
                    self._request(
                        lambda success, error: self._controller.delete_task_async(
                            selected, task.id, success, error
                        ), lambda _result: self._refresh_tasks(), "Excluindo tarefa...",
                    )
            dialog.connect("response", delete)
            dialog.present(self)
        elif action == "subtask":
            dialog = Adw.AlertDialog.new("Adicionar subtarefa", f'Em “{task.title}”.')
            entry = Gtk.Entry(placeholder_text="Título da subtarefa", activates_default=True)
            entry.set_max_length(1024)
            dialog.set_extra_child(entry)
            dialog.add_response("cancel", "Cancelar")
            dialog.add_response("create", "Adicionar")
            dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_default_response("create")
            dialog.set_close_response("cancel")
            dialog.set_response_enabled("create", False)
            entry.connect("changed", lambda widget: dialog.set_response_enabled(
                "create", bool(widget.get_text().strip())
            ))
            def create(_dialog, response):
                if response == "create":
                    self._request(
                        lambda success, error: self._controller.create_subtask_async(
                            selected, task.id, entry.get_text(), success, error
                        ), lambda _result: self._refresh_tasks(), "Criando subtarefa...",
                    )
            dialog.connect("response", create)
            dialog.present(self)
        elif action == "move":
            lists = [item for item in self._controller.get_lists()
                     if item.source == selected.source and item.id != selected.id]
            if not lists:
                self._show_error("Crie outra lista nesta conta ou dispositivo para mover a tarefa.")
                return
            dialog = Adw.AlertDialog.new("Mover tarefa", "Escolha uma lista da mesma conta ou dispositivo.")
            group = Adw.PreferencesGroup()
            choice = Adw.ComboRow(title="Lista", model=Gtk.StringList.new([item.name for item in lists]))
            group.add(choice)
            dialog.set_extra_child(group)
            dialog.add_response("cancel", "Cancelar")
            dialog.add_response("move", "Mover")
            dialog.set_response_appearance("move", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_default_response("move")
            dialog.set_close_response("cancel")
            def move(_dialog, response):
                if response == "move":
                    self._request(
                        lambda success, error: self._controller.move_task_async(
                            selected, task.id, lists[choice.get_selected()], success, error
                        ), lambda _result: self._refresh_tasks(), "Movendo tarefa...",
                    )
            dialog.connect("response", move)
            dialog.present(self)

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
        selected = self._controller.selected_list
        self._task_panel.set_list(selected)
        title = selected.name if selected else "Tarefas"
        self._content_page.set_title(title)
        self._content_title.set_title(title)
        self._content_title.set_subtitle(
            "Neste dispositivo" if selected and selected.source == "local"
            else "Google Tasks" if selected else ""
        )
        if selected is None:
            self._split_view.set_show_content(False)
            self._task_panel.show_message(
                "Selecione uma lista para ver as tarefas"
                if self._controller.get_lists() else "Crie uma lista para começar"
            )
            return

        # The remote cache is read immediately; selecting a list causes no HTTP call.
        cached = self._controller.cached_tasks(selected)
        if cached is not None:
            if self._settings.get_boolean("show-completed"):
                self._task_panel.show_tasks(cached)
            else:
                self._task_panel.show_tasks(
                    [task for task in cached if not task.completed],
                    empty_message="Nenhuma tarefa pendente",
                )
        elif self._controller.is_syncing(selected.source):
            self._task_panel.show_message("Sincronizando tarefas...")
        else:
            self._task_panel.show_message(
                "Nenhuma cópia local disponível. Atualize para sincronizar."
            )
