import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio

from gtasks.controllers.task_controller import TaskController
from gtasks.repositories.memory import InMemoryTaskRepository
from gtasks.services.task_service import TaskService
from gtasks.views.main_window import MainWindow


class GTasksApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id="io.github.rafatosta.gtasks",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        storage = InMemoryTaskRepository()
        self._controller = TaskController(TaskService(lists=storage, tasks=storage))

    def do_activate(self) -> None:
        window = self.props.active_window
        if window is None:
            window = MainWindow(application=self, controller=self._controller)
        window.present()
