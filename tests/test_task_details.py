import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from gtasks.models.google_account import GoogleAccount
from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.repositories.cache import RemoteTaskCache
from gtasks.repositories.google import GoogleTasksRepository
from gtasks.repositories.memory import InMemoryTaskRepository
from gtasks.repositories.registry import RepositoryRegistry
from gtasks.repositories.sqlite import SQLiteTaskRepository
from gtasks.services.task_service import TaskService


class TaskDetailsTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'tasks.db'
        self.local = SQLiteTaskRepository(self.path)
        self.addCleanup(self.local._connection.close)
        self.service = TaskService(RepositoryRegistry({'local': self.local}))
        self.list = self.service.create_list('First')
        self.task = self.service.create_task(self.list, 'Original')

    def test_details_and_date_persist_through_completion_and_restart(self):
        updated = self.service.update_task(self.list, self.task.id, ' New ', 'Notes\nsecond line', '2026-10-20')
        completed = self.service.set_completed(self.list, self.task.id, True)
        reopened = SQLiteTaskRepository(self.path)
        self.addCleanup(reopened._connection.close)
        self.assertEqual(reopened.list_tasks(self.list.id), [replace(updated, completed=True)])
        self.assertEqual(completed.notes, updated.notes)
        self.service.update_task(self.list, self.task.id, 'New', '', None)
        self.assertEqual(self.service.get_tasks(self.list)[0].notes, '')
        self.assertIsNone(self.service.get_tasks(self.list)[0].due)

    def test_subtasks_move_and_delete_with_parent(self):
        child = self.service.create_subtask(self.list, self.task.id, 'Child')
        destination = self.service.create_list('Second')
        self.service.move_task(self.list, self.task.id, destination)
        self.assertEqual(self.service.get_tasks(self.list), [])
        moved = self.service.get_tasks(destination)
        self.assertEqual({task.id for task in moved}, {self.task.id, child.id})
        self.assertEqual(next(task for task in moved if task.id == child.id).parent, self.task.id)
        self.service.delete_task(destination, self.task.id)
        self.assertEqual(self.service.get_tasks(destination), [])

    def test_moving_child_makes_it_top_level(self):
        child = self.service.create_subtask(self.list, self.task.id, 'Child')
        destination = self.service.create_list('Second')
        moved = self.service.move_task(self.list, child.id, destination)
        self.assertIsNone(moved.parent)
        self.assertEqual(self.service.get_tasks(self.list), [self.task])

    def test_invalid_edit_preserves_original(self):
        for title, notes, due in [('', '', None), ('x' * 1025, '', None),
                                  ('Title', 'x' * 8193, None), ('Title', '', '2026-02-30')]:
            with self.assertRaises(ValueError):
                self.service.update_task(self.list, self.task.id, title, notes, due)
        self.assertEqual(self.service.get_tasks(self.list), [self.task])

    def test_moves_between_accounts_are_rejected(self):
        with self.assertRaises(ValueError):
            self.service.move_task(self.list, self.task.id, TaskList('other', 'Other', 'google:a'))
        self.assertEqual(self.service.get_tasks(self.list), [self.task])

    def test_local_schema_upgrade_preserves_existing_tasks(self):
        path = Path(self.folder.name) / 'old.db'
        with closing(sqlite3.connect(path)) as db:
            db.executescript("""CREATE TABLE task_lists (id TEXT PRIMARY KEY, name TEXT NOT NULL);
                CREATE TABLE tasks (id TEXT PRIMARY KEY, list_id TEXT NOT NULL,
                                    title TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0);
                INSERT INTO task_lists VALUES ('l', 'Old');
                INSERT INTO tasks VALUES ('t', 'l', 'Keep', 1);""")
        repository = SQLiteTaskRepository(path)
        self.addCleanup(repository._connection.close)
        self.assertEqual(repository.list_tasks('l'), [Task('t', 'l', 'Keep', True)])
        repository.update_task('l', 't', 'Keep', 'Added later', '2026-10-20')
        self.assertEqual(repository.list_tasks('l')[0].notes, 'Added later')

    def test_remote_metadata_survives_worker_writes_moves_and_deletion(self):
        remote = InMemoryTaskRepository('google:a')
        cache = RemoteTaskCache(self.path)
        registry = RepositoryRegistry({'local': self.local}, cache=cache)
        registry.register_remote([('google:a', 'A', remote)])
        service = TaskService(registry)
        first = service.create_list('Remote', 'google:a')
        second = service.create_list('Destination', 'google:a')
        task = service.create_task(first, 'Task')
        with ThreadPoolExecutor(max_workers=1) as worker:
            updated = worker.submit(service.update_task, first, task.id, 'Edited', 'Notes', '2026-10-20').result()
            child = worker.submit(service.create_subtask, first, task.id, 'Child').result()
            completed = worker.submit(service.set_completed, first, task.id, True).result()
            self.assertEqual(completed.notes, updated.notes)
            self.assertEqual(RemoteTaskCache(self.path).tasks(first), [completed, child])
            with patch.object(remote, 'update_task', side_effect=RuntimeError('offline')):
                with self.assertRaises(RuntimeError):
                    worker.submit(service.update_task, first, task.id, 'Bad', '', None).result()
            self.assertEqual(cache.tasks(first), [completed, child])
            for method, arguments in (
                ('delete_task', (first, task.id)),
                ('move_task', (first, task.id, second)),
            ):
                with patch.object(remote, method, side_effect=RuntimeError('offline')):
                    with self.assertRaises(RuntimeError):
                        worker.submit(getattr(service, method), *arguments).result()
                self.assertEqual(cache.tasks(first), [completed, child])
                self.assertEqual(cache.tasks(second), [])
            worker.submit(service.move_task, first, task.id, second).result()
            self.assertEqual(cache.tasks(first), [])
            self.assertEqual(len(cache.tasks(second)), 2)
            worker.submit(service.delete_task, second, task.id).result()
            self.assertEqual(cache.tasks(second), [])

    def test_remote_schema_upgrade_preserves_existing_snapshot(self):
        path = Path(self.folder.name) / 'old-cache.db'
        with closing(sqlite3.connect(path)) as db:
            db.executescript("""CREATE TABLE remote_lists (
                    source TEXT, id TEXT, name TEXT, PRIMARY KEY(source, id));
                CREATE TABLE remote_tasks (
                    source TEXT, list_id TEXT, id TEXT, title TEXT,
                    completed INTEGER, position INTEGER, PRIMARY KEY(source, list_id, id));
                CREATE TABLE remote_loaded (source TEXT, list_id TEXT, PRIMARY KEY(source, list_id));
                INSERT INTO remote_lists VALUES ('google:a', 'l', 'List');
                INSERT INTO remote_tasks VALUES ('google:a', 'l', 't', 'Keep', 0, 0);
                INSERT INTO remote_loaded VALUES ('google:a', 'l');""")
        cache = RemoteTaskCache(path)
        item = TaskList('l', 'List', 'google:a')
        self.assertEqual(cache.tasks(item), [Task('t', 'l', 'Keep')])
        updated = Task('t', 'l', 'Keep', notes='New details', due='2026-10-20')
        cache.update_task(item, updated)
        self.assertEqual(RemoteTaskCache(path).tasks(item), [updated])

    def test_cached_subtree_delete_is_scoped_to_account(self):
        cache = RemoteTaskCache(self.path)
        for source in ('google:a', 'google:b'):
            item = TaskList('same-list', 'List', source)
            cache.replace_lists(source, [item])
            cache.replace_tasks(item, [Task('parent', item.id, 'Parent'),
                                       Task('child', item.id, 'Child', parent='parent')])
        cache.delete_task(TaskList('same-list', 'List', 'google:a'), 'parent')
        self.assertEqual(cache.tasks(TaskList('same-list', 'List', 'google:a')), [])
        self.assertEqual(len(cache.tasks(TaskList('same-list', 'List', 'google:b'))), 2)


class GoogleTaskDetailsTest(unittest.TestCase):
    def setUp(self):
        self.repo = GoogleTasksRepository(GoogleAccount('a', 'a@example.com', '/a'), None)
        self.response = {'id': 't/id', 'title': 'Task', 'notes': 'Notes',
                         'due': '2026-10-20T00:00:00.000Z', 'parent': 'p', 'status': 'completed'}

    def test_patch_encodes_paths_and_date_and_parses_fields(self):
        with patch.object(self.repo, '_request', return_value=self.response) as request:
            task = self.repo.update_task('l/id', 't/id', 'Task', 'Notes', '2026-10-20')
            request.assert_called_once_with('PATCH', '/lists/l%2Fid/tasks/t%2Fid',
                {'title': 'Task', 'notes': 'Notes', 'due': '2026-10-20T00:00:00.000Z'})
            self.assertEqual(task.due, '2026-10-20')
            self.assertEqual(task.parent, 'p')
            self.assertTrue(task.completed)
        with patch.object(self.repo, '_request', return_value={'id': 't/id', 'title': 'Task'}) as request:
            self.repo.update_task('l/id', 't/id', 'Task', '', None)
            self.assertEqual(request.call_args.args[2], {'title': 'Task', 'notes': '', 'due': None})

    def test_assigned_task_notes_can_be_left_unchanged(self):
        with patch.object(self.repo, '_request', return_value=self.response) as request:
            self.repo.update_task('l', 't', 'Task', None, None)
            self.assertNotIn('notes', request.call_args.args[2])

    def test_subtask_uses_parent_query_and_move_uses_destination(self):
        with patch.object(self.repo, '_request', return_value=self.response) as request:
            self.repo.create_subtask('l/id', 'p/id', 'Child')
            request.assert_called_once_with('POST', '/lists/l%2Fid/tasks', {'title': 'Child'}, params={'parent': 'p/id'})
        with patch.object(self.repo, '_request', return_value=self.response) as request:
            task = self.repo.move_task('l/id', 't/id', 'dest/id')
            request.assert_called_once_with('POST', '/lists/l%2Fid/tasks/t%2Fid/move', params={'destinationTasklist': 'dest/id'})
            self.assertEqual(task.list_id, 'dest/id')
        with patch.object(self.repo, '_request', return_value={}) as request:
            self.repo.delete_task('l/id', 't/id')
            request.assert_called_once_with('DELETE', '/lists/l%2Fid/tasks/t%2Fid')
