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
from gtasks.views.preferences_dialog import create_preferences_dialog
from gtasks.views.shortcuts_dialog import create_shortcuts_dialog


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

        self._settings = Gio.Settings.new("io.github.rafatosta.gtasks")

        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self._show_preferences)
        self.add_action(preferences_action)
        self.set_accels_for_action("app.preferences", ["<Primary>comma"])

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self._quit)
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Primary>q"])

        shortcuts_action = Gio.SimpleAction.new("shortcuts", None)
        shortcuts_action.connect("activate", self._show_shortcuts)
        self.add_action(shortcuts_action)
        self.set_accels_for_action("app.shortcuts", ["<Primary>question", "<Primary>F1"])
        self.set_accels_for_action("win.close", ["<Primary>w"])
        self.set_accels_for_action("win.refresh", ["<Primary>r", "F5"])

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
            window = MainWindow(
                application=self, controller=self._controller, settings=self._settings
            )
        window.present()

    def _show_about(self, _action: Gio.SimpleAction, _parameter) -> None:
        window = self.props.active_window
        if window is None:
            return

        create_about_dialog(version=self.VERSION).present(window)

    def _show_preferences(self, _action: Gio.SimpleAction, _parameter) -> None:
        window = self.props.active_window
        if window is not None:
            create_preferences_dialog(self._settings).present(window)

    def _quit(self, _action: Gio.SimpleAction, _parameter) -> None:
        # Close windows through their normal cleanup path before exiting.
        for window in self.get_windows():
            window.close()
        self._controller.close()
        self.quit()

    def _show_shortcuts(self, _action: Gio.SimpleAction, _parameter) -> None:
        window = self.props.active_window
        if window is not None:
            create_shortcuts_dialog().present(window)
