import tempfile
import unittest
from pathlib import Path

from gtasks.controllers.task_controller import TaskController
from gtasks.repositories.memory import InMemoryTaskRepository
from gtasks.repositories.sqlite import SQLiteTaskRepository
from gtasks.services.task_service import TaskService


class TasksTest(unittest.TestCase):
    def setUp(self) -> None:
        repository = InMemoryTaskRepository()
        self.controller = TaskController(TaskService({"local": repository}))

    def test_creating_list_starts_empty(self) -> None:
        task_list = self.controller.create_list("Trabalho")
        self.assertEqual(task_list.name, "Trabalho")
        self.assertEqual(task_list.source, "local")
        self.assertEqual(self.controller.get_tasks(), [])

    def test_tasks_belong_to_their_list(self) -> None:
        first = self.controller.create_list("Trabalho")
        task = self.controller.create_task("Revisar documentos")
        second = self.controller.create_list("Pessoal")
        self.controller.create_task("Comprar pão")
        self.assertEqual(len(self.controller.get_tasks()), 1)
        self.controller.select_list(first.id)
        self.assertEqual(self.controller.get_tasks(), [task])
        self.controller.select_list(second.id)
        self.assertEqual(self.controller.get_tasks()[0].title, "Comprar pão")

    def test_can_complete_task(self) -> None:
        self.controller.create_list("Tarefas")
        task = self.controller.create_task("Teste")
        self.controller.set_completed(task.id, True)
        self.assertTrue(self.controller.get_tasks()[0].completed)

    def test_empty_names_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.controller.create_list("  ")
        self.controller.create_list("Válida")
        with self.assertRaises(ValueError):
            self.controller.create_task("   ")

    def test_sync_source_is_not_available_yet(self) -> None:
        self.assertFalse(self.controller.has_source("google"))
        with self.assertRaises(ValueError):
            self.controller.create_list("Remota", "google")

    def test_sqlite_persists_lists_and_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tasks.db"
            first = TaskController(TaskService({"local": SQLiteTaskRepository(path)}))
            task_list = first.create_list("Pessoal")
            task = first.create_task("Comprar pão")
            first.set_completed(task.id, True)

            reopened = TaskController(TaskService({"local": SQLiteTaskRepository(path)}))
            reopened.select_list(task_list.id)
            self.assertEqual(reopened.get_lists(), [task_list])
            self.assertEqual(reopened.get_tasks()[0].title, task.title)
            self.assertTrue(reopened.get_tasks()[0].completed)

    def test_list_sources_can_coexist(self) -> None:
        local = InMemoryTaskRepository(source="local")
        google = InMemoryTaskRepository(source="google")
        service = TaskService({"local": local, "google": google})
        controller = TaskController(service)

        personal = controller.create_list("Pessoal", "local")
        controller.create_task("Comprar pão")
        work = controller.create_list("Trabalho", "google")
        controller.create_task("Reunião")
        controller.cache_remote_lists("google", google.list_lists())

        self.assertEqual([item.source for item in controller.get_lists()], ["local", "google"])
        controller.select_list(personal.id, "local")
        self.assertEqual([task.title for task in controller.get_tasks()], ["Comprar pão"])
        controller.select_list(work.id, "google")
        self.assertEqual([task.title for task in controller.get_tasks()], ["Reunião"])


if __name__ == "__main__":
    unittest.main()
