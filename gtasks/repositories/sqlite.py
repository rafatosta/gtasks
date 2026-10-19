import sqlite3
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.repositories.base import TaskRepository
from gtasks.repositories.task_details import ensure_details_column, encode_details, decode_details


class SQLiteTaskRepository(TaskRepository):
    """Persistent storage for lists and tasks saved on this device."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path)
        self._connection.execute("PRAGMA foreign_keys = ON")
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS task_lists (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    list_id TEXT NOT NULL REFERENCES task_lists(id),
                    title TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0
                );
                """
            )

            ensure_details_column(self._connection, "tasks")

    def list_lists(self) -> list[TaskList]:
        rows = self._connection.execute(
            "SELECT id, name FROM task_lists ORDER BY rowid"
        ).fetchall()
        return [TaskList(id=row[0], name=row[1]) for row in rows]

    def create_list(self, name: str) -> TaskList:
        item = TaskList(id=str(uuid4()), name=name)
        with self._connection:
            self._connection.execute(
                "INSERT INTO task_lists (id, name) VALUES (?, ?)",
                (item.id, item.name),
            )
        return item

    def rename_list(self, list_id: str, name: str) -> TaskList:
        with self._connection:
            cursor = self._connection.execute(
                "UPDATE task_lists SET name = ? WHERE id = ?", (name, list_id)
            )
            if cursor.rowcount == 0:
                raise KeyError(list_id)
        return TaskList(id=list_id, name=name)

    def delete_list(self, list_id: str) -> None:
        with self._connection:
            self._connection.execute("DELETE FROM tasks WHERE list_id = ?", (list_id,))
            cursor = self._connection.execute("DELETE FROM task_lists WHERE id = ?", (list_id,))
            if cursor.rowcount == 0:
                raise KeyError(list_id)

    def list_tasks(self, list_id: str) -> list[Task]:
        rows = self._connection.execute(
            "SELECT id, title, completed, details FROM tasks WHERE list_id = ? ORDER BY rowid",
            (list_id,),
        ).fetchall()
        return [
            Task(id=row[0], list_id=list_id, title=row[1], completed=bool(row[2]),
                 **decode_details(row[3]))
            for row in rows
        ]

    def create_task(self, list_id: str, title: str) -> Task:
        task = Task(id=str(uuid4()), list_id=list_id, title=title)
        with self._connection:
            self._connection.execute(
                "INSERT INTO tasks (id, list_id, title) VALUES (?, ?, ?)",
                (task.id, task.list_id, task.title),
            )
        return task

    def set_completed(self, list_id: str, task_id: str, completed: bool) -> Task:
        with self._connection:
            cursor = self._connection.execute(
                "UPDATE tasks SET completed = ? WHERE id = ? AND list_id = ?",
                (int(completed), task_id, list_id),
            )
        if cursor.rowcount == 0:
            raise KeyError(task_id)
        return self._find_task(list_id, task_id)

    def _find_task(self, list_id, task_id) -> Task:
        row = self._connection.execute(
            "SELECT title, completed, details FROM tasks WHERE list_id = ? AND id = ?",
            (list_id, task_id),
        ).fetchone()
        if row is None:
            raise KeyError(task_id)
        return Task(id=task_id, list_id=list_id, title=row[0], completed=bool(row[1]),
                    **decode_details(row[2]))

    def update_task(self, list_id: str, task_id: str, title: str,
                    notes: str | None, due: str | None) -> Task:
        original = self._find_task(list_id, task_id)
        task = replace(original, title=title, notes=original.notes if notes is None else notes, due=due)
        with self._connection:
            self._connection.execute(
                "UPDATE tasks SET title = ?, details = ? WHERE list_id = ? AND id = ?",
                (title, encode_details(task), list_id, task_id),
            )
        return task

    def _subtree(self, list_id, task_id) -> list[Task]:
        self._find_task(list_id, task_id)
        tasks = self.list_tasks(list_id)
        ids = {task_id}
        while True:
            expanded = ids | {task.id for task in tasks if task.parent in ids}
            if expanded == ids:
                return [task for task in tasks if task.id in ids]
            ids = expanded

    def delete_task(self, list_id: str, task_id: str) -> None:
        tasks = self._subtree(list_id, task_id)
        with self._connection:
            self._connection.executemany(
                "DELETE FROM tasks WHERE list_id = ? AND id = ?",
                [(list_id, task.id) for task in tasks],
            )

    def create_subtask(self, list_id: str, parent: str, title: str) -> Task:
        self._find_task(list_id, parent)
        task = Task(id=str(uuid4()), list_id=list_id, title=title, parent=parent)
        with self._connection:
            self._connection.execute(
                "INSERT INTO tasks (id, list_id, title, details) VALUES (?, ?, ?, ?)",
                (task.id, list_id, title, encode_details(task)),
            )
        return task

    def move_task(self, list_id: str, task_id: str, destination: str) -> Task:
        if not any(item.id == destination for item in self.list_lists()):
            raise KeyError(destination)
        moved = [replace(task, list_id=destination,
                         parent=None if task.id == task_id else task.parent)
                 for task in self._subtree(list_id, task_id)]
        with self._connection:
            self._connection.executemany(
                "UPDATE tasks SET list_id = ?, details = ? WHERE id = ? AND list_id = ?",
                [(destination, encode_details(task), task.id, list_id) for task in moved],
            )
        return next(task for task in moved if task.id == task_id)
