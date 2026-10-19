import queue
import unittest

from gtasks.controllers.task_controller import TaskController
from gtasks.repositories.memory import InMemoryTaskRepository
from gtasks.repositories.registry import RepositoryRegistry
from gtasks.services.task_service import TaskService


class RegistryTest(unittest.TestCase):
    def test_sources_and_cached_remote_lists(self) -> None:
        local = InMemoryTaskRepository()
        remote = InMemoryTaskRepository("google:account1")
        registry = RepositoryRegistry({"local": local})
        registry.register_remote([("google:account1", "test@example.invalid", remote)])
        self.assertIs(registry.resolve("local"), local)
        self.assertIs(registry.resolve("google:account1"), remote)

        remote_list = remote.create_list("Trabalho")
        self.assertEqual(len(registry.list_lists()), 0)
        registry.cache_remote_lists("google:account1", [remote_list])
        self.assertEqual(registry.list_lists(), [remote_list])
        registry.register_remote([])
        self.assertEqual(registry.list_lists(), [])

    def test_remote_callbacks_are_dispatched_before_updating_controller(self) -> None:
        callbacks = queue.Queue()
        local = InMemoryTaskRepository()
        remote = InMemoryTaskRepository("google:account1")
        registry = RepositoryRegistry(
            {"local": local},
            discover_remote=lambda: [
                ("google:account1", "test@example.invalid", remote)
            ],
        )
        controller = TaskController(
            TaskService(registry),
            dispatch=lambda callback: callbacks.put(callback),
        )
        results = []
        errors = []
        try:
            controller.discover_remote_async(results.append, errors.append)
            # Simulate the GTK main loop processing its scheduled callback.
            callbacks.get(timeout=5)()
            self.assertFalse(errors)
            self.assertEqual(results, [[("google:account1", "test@example.invalid")]])
            self.assertTrue(controller.has_source("google:account1"))
        finally:
            controller.close()


if __name__ == "__main__":
    unittest.main()
