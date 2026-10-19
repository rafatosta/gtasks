import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gtasks.models.google_account import GoogleAccount
from gtasks.repositories.cache import RemoteTaskCache
from gtasks.repositories.google import GoogleTasksRepository
from gtasks.repositories.memory import InMemoryTaskRepository
from gtasks.repositories.registry import RepositoryRegistry
from gtasks.repositories.sqlite import SQLiteTaskRepository
from gtasks.services.task_service import TaskService


class ListManagementTest(unittest.TestCase):
    def test_local_changes_persist_and_delete_tasks(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "local.db"
            repo = SQLiteTaskRepository(path)
            self.addCleanup(repo._connection.close)
            service = TaskService(RepositoryRegistry({"local": repo}))
            item = service.create_list("Original")
            task = service.create_task(item, "Preservada")
            updated = service.rename_list(item, "  Novo nome  ")
            renamed = SQLiteTaskRepository(path)
            self.addCleanup(renamed._connection.close)
            self.assertEqual(renamed.list_lists(), [updated])
            self.assertEqual(service.get_tasks(updated), [task])
            service.delete_list(updated)
            reopened = SQLiteTaskRepository(path)
            self.addCleanup(reopened._connection.close)
            self.assertEqual(reopened.list_lists(), [])
            self.assertEqual(reopened.list_tasks(item.id), [])

    def test_remote_cache_preserves_tasks_on_rename_and_clears_on_delete(self):
        with tempfile.TemporaryDirectory() as folder:
            cache = RemoteTaskCache(Path(folder) / "cache.db")
            remote = InMemoryTaskRepository("google:test")
            registry = RepositoryRegistry({"local": InMemoryTaskRepository(),
                                           "google:test": remote}, cache=cache)
            service = TaskService(registry)
            item = service.create_list("Original", "google:test")
            task = service.create_task(item, "Tarefa")
            updated = service.rename_list(item, "Novo")
            self.assertEqual(cache.lists(item.source), [updated])
            self.assertEqual(cache.tasks(updated), [task])
            remaining = remote.create_list("Outra lista")
            with patch.object(remote, "delete_list", side_effect=RuntimeError("offline")):
                with self.assertRaises(RuntimeError):
                    service.delete_list(updated)
            self.assertEqual(cache.lists(item.source), [updated])
            service.delete_list(updated)
            self.assertEqual(service.get_lists(), [remaining])
            self.assertEqual(cache.lists(item.source), [remaining])
            self.assertIsNone(cache.tasks(updated))

    def test_last_remote_list_cannot_be_deleted_even_with_stale_cache(self):
        remote = InMemoryTaskRepository("google:a")
        other = InMemoryTaskRepository("google:b")
        registry = RepositoryRegistry({"local": InMemoryTaskRepository(),
                                       "google:a": remote, "google:b": other})
        service = TaskService(registry)
        item = service.create_list("Única", "google:a")
        stale = service.create_list("Removida fora do app", "google:a")
        service.create_list("Outra conta", "google:b")
        service.create_list("Local")
        remote.delete_list(stale.id)
        with patch.object(remote, "delete_list", wraps=remote.delete_list) as delete:
            with self.assertRaisesRegex(ValueError, "última lista"):
                service.delete_list(item)
            delete.assert_not_called()
        self.assertEqual(remote.list_lists(), [item])

    def test_deleting_one_of_two_lists_protects_remaining_list(self):
        remote = InMemoryTaskRepository("google:a")
        service = TaskService(RepositoryRegistry({"local": InMemoryTaskRepository(),
                                                 "google:a": remote}))
        first = service.create_list("Primeira", "google:a")
        second = service.create_list("Segunda", "google:a")
        service.delete_list(first)
        with self.assertRaisesRegex(ValueError, "última lista"):
            service.delete_list(second)
        self.assertEqual(service.get_lists(), [second])

    def test_empty_rename_is_rejected(self):
        service = TaskService(RepositoryRegistry({"local": InMemoryTaskRepository()}))
        item = service.create_list("Original")
        with self.assertRaises(ValueError):
            service.rename_list(item, "   ")
        self.assertEqual(service.get_lists(), [item])

    def test_google_rename_and_delete_use_encoded_list_path(self):
        repo = GoogleTasksRepository(GoogleAccount("a", "test@example.com", "/a"), None)
        with patch.object(repo, "_request", return_value={"id": "a/b", "title": "Novo"}) as request:
            item = repo.rename_list("a/b", "Novo")
            request.assert_called_once_with("PATCH", "/users/@me/lists/a%2Fb", {"title": "Novo"})
            self.assertEqual(item.name, "Novo")
        with patch.object(repo, "_request", return_value={}) as request:
            repo.delete_list("a/b")
            request.assert_called_once_with("DELETE", "/users/@me/lists/a%2Fb")
