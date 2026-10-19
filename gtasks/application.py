import os
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio

from gtasks.controllers.task_controller import TaskController
from gtasks.repositories.sqlite import SQLiteTaskRepository
from gtasks.services.task_service import TaskService
from gtasks.views.main_window import MainWindow


class GTasksApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id="io.github.rafatosta.gtasks",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        data_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        storage = SQLiteTaskRepository(data_dir / "gtasks" / "tasks.db")
        self._controller = TaskController(TaskService({"local": storage}))

    def do_activate(self) -> None:
        window = self.props.active_window
        if window is None:
            window = MainWindow(application=self, controller=self._controller)
        window.present()
