import sqlite3
from pathlib import Path
from uuid import uuid4

from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.repositories.base import TaskRepository


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

    def list_tasks(self, list_id: str) -> list[Task]:
        rows = self._connection.execute(
            "SELECT id, title, completed FROM tasks WHERE list_id = ? ORDER BY rowid",
            (list_id,),
        ).fetchall()
        return [
            Task(id=row[0], list_id=list_id, title=row[1], completed=bool(row[2]))
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
        row = self._connection.execute(
            "SELECT title FROM tasks WHERE id = ? AND list_id = ?",
            (task_id, list_id),
        ).fetchone()
        return Task(id=task_id, list_id=list_id, title=row[0], completed=completed)
