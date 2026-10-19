import tempfile
import unittest
from pathlib import Path

from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.repositories.cache import RemoteTaskCache
from gtasks.repositories.memory import InMemoryTaskRepository
from gtasks.repositories.registry import RepositoryRegistry
from gtasks.repositories.sqlite import SQLiteTaskRepository
from gtasks.services.task_service import TaskService


class OfflineCacheTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "tasks.db"
        self.local = SQLiteTaskRepository(self.path)
        self.cache = RemoteTaskCache(self.path)

    def tearDown(self):
        self.local._connection.close()
        self.folder.cleanup()

    def test_empty_list_is_distinct_from_list_not_yet_loaded(self):
        task_list = TaskList(id="first", name="Work", source="google:a")
        self.cache.replace_lists("google:a", [task_list])
        self.assertIsNone(self.cache.tasks(task_list))
        self.cache.replace_tasks(task_list, [])
        self.assertEqual(self.cache.tasks(task_list), [])

    def test_cached_tasks_survive_restart_and_sources_are_isolated(self):
        a = TaskList(id="same", name="Account A", source="google:a")
        b = TaskList(id="same", name="Account B", source="google:b")
        self.cache.replace_lists("google:a", [a])
        self.cache.replace_lists("google:b", [b])
        self.cache.replace_tasks(a, [Task("task", a.id, "A task")])
        self.cache.replace_tasks(b, [Task("task", b.id, "B task", True)])

        reopened = RemoteTaskCache(self.path)
        self.assertEqual(reopened.tasks(a)[0].title, "A task")
        self.assertEqual(reopened.tasks(b)[0].title, "B task")
        self.assertTrue(reopened.tasks(b)[0].completed)
        self.assertEqual(self.local.list_lists(), [])

    def test_failed_sync_preserves_old_data(self):
        class FailingRepository(InMemoryTaskRepository):
            fail = False

            def list_tasks(self, list_id):
                if self.fail:
                    raise RuntimeError("offline")
                return super().list_tasks(list_id)

        remote = FailingRepository("google:a")
        task_list = remote.create_list("Work")
        remote.create_task(task_list.id, "Earlier")
        registry = RepositoryRegistry({"local": self.local}, cache=self.cache)
        registry.register_remote([("google:a", "A", remote)])
        service = TaskService(registry)
        service.sync_source("google:a", lambda _item: None)
        self.assertEqual(self.cache.tasks(task_list)[0].title, "Earlier")

        remote.create_task(task_list.id, "Newer")
        remote.fail = True
        with self.assertRaisesRegex(RuntimeError, "offline"):
            service.sync_source("google:a", lambda _item: None)
        self.assertEqual(
            [task.title for task in self.cache.tasks(task_list)], ["Earlier"]
        )

    def test_successful_writes_immediately_update_cache(self):
        remote = InMemoryTaskRepository("google:a")
        registry = RepositoryRegistry({"local": self.local}, cache=self.cache)
        registry.register_remote([("google:a", "A", remote)])
        service = TaskService(registry)

        task_list = service.create_list("Work", "google:a")
        self.assertEqual(self.cache.tasks(task_list), [])
        task = service.create_task(task_list, "New task")
        self.assertEqual(self.cache.tasks(task_list), [task])
        service.set_completed(task_list, task.id, True)
        self.assertTrue(self.cache.tasks(task_list)[0].completed)

    def test_deleted_lists_remove_only_their_cached_tasks(self):
        a = TaskList("one", "First", "google:a")
        b = TaskList("two", "Second", "google:a")
        self.cache.replace_lists("google:a", [a, b])
        self.cache.replace_tasks(a, [Task("one", a.id, "Old")])
        self.cache.replace_tasks(b, [Task("two", b.id, "Keep")])
        self.cache.replace_lists("google:a", [b])
        self.assertIsNone(self.cache.tasks(a))
        self.assertEqual(self.cache.tasks(b)[0].title, "Keep")

    def test_cache_for_removed_account_is_cleared(self):
        remote = InMemoryTaskRepository("google:a")
        registry = RepositoryRegistry({"local": self.local}, cache=self.cache)
        registry.register_remote([("google:a", "A", remote)])
        task_list = remote.create_list("Work")
        registry.cache_remote_lists("google:a", [task_list])
        self.assertEqual(self.cache.lists("google:a"), [task_list])
        registry.register_remote([])
        self.assertEqual(self.cache.lists("google:a"), [])


if __name__ == "__main__":
    unittest.main()
