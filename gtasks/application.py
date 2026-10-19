import os
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib

from gtasks.auth.goa import GoaAuthProvider
from gtasks.controllers.task_controller import TaskController
from gtasks.repositories.google import GoogleTasksRepository
from gtasks.repositories.cache import RemoteTaskCache
from gtasks.repositories.sqlite import SQLiteTaskRepository
from gtasks.repositories.registry import RepositoryRegistry
from gtasks.services.task_service import TaskService
from gtasks.views.main_window import MainWindow
from gtasks.views.about_dialog import create_about_dialog


class GTasksApplication(Adw.Application):
    VERSION = "0.1.0"
    def __init__(self) -> None:
        super().__init__(
            application_id="io.github.rafatosta.gtasks",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        data_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        database = data_dir / "gtasks" / "tasks.db"
        storage = SQLiteTaskRepository(database)
        cache = RemoteTaskCache(database)
        auth = GoaAuthProvider()

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._show_about)
        self.add_action(about_action)

        def discover():
            return [
                (account.source, account.identity, GoogleTasksRepository(account, auth))
                for account in auth.list_accounts()
            ]

        registry = RepositoryRegistry(
            {"local": storage}, discover_remote=discover, cache=cache
        )
        service = TaskService(registry)
        self._controller = TaskController(
            service,
            dispatch=lambda callback: GLib.idle_add(
                lambda: (callback(), GLib.SOURCE_REMOVE)[1]
            ),
        )

    def do_activate(self) -> None:
        window = self.props.active_window
        if window is None:
            window = MainWindow(application=self, controller=self._controller)
        window.present()

    def _show_about(self, _action: Gio.SimpleAction, _parameter) -> None:
        window = self.props.active_window
        if window is None:
            return

        create_about_dialog(version=self.VERSION).present(window)
