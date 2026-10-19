"""Persistent read-through snapshots of remote accounts; local tasks remain separate."""

import sqlite3
from contextlib import closing
from pathlib import Path

from gtasks.models.task import Task
from gtasks.models.task_list import TaskList


class RemoteTaskCache:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with closing(self._connect()) as db:
            with db:
                db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS remote_lists (
                        source TEXT NOT NULL,
                        id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        PRIMARY KEY (source, id)
                    );
                    CREATE TABLE IF NOT EXISTS remote_tasks (
                        source TEXT NOT NULL,
                        list_id TEXT NOT NULL,
                        id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        completed INTEGER NOT NULL,
                        position INTEGER NOT NULL,
                        PRIMARY KEY (source, list_id, id),
                        FOREIGN KEY (source, list_id)
                            REFERENCES remote_lists(source, id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS remote_loaded (
                        source TEXT NOT NULL,
                        list_id TEXT NOT NULL,
                        PRIMARY KEY (source, list_id),
                        FOREIGN KEY (source, list_id)
                            REFERENCES remote_lists(source, id) ON DELETE CASCADE
                    );
                    """
                )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self._path, timeout=15)
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def lists(self, source: str) -> list[TaskList]:
        with closing(self._connect()) as db:
            rows = db.execute(
                "SELECT id, name FROM remote_lists WHERE source = ? ORDER BY rowid",
                (source,),
            ).fetchall()
        return [TaskList(id=id, name=name, source=source) for id, name in rows]

    def tasks(self, task_list: TaskList) -> list[Task] | None:
        with closing(self._connect()) as db:
            loaded = db.execute(
                "SELECT 1 FROM remote_loaded WHERE source = ? AND list_id = ?",
                (task_list.source, task_list.id),
            ).fetchone()
            if not loaded:
                return None
            rows = db.execute(
                """SELECT id, title, completed FROM remote_tasks
                   WHERE source = ? AND list_id = ? ORDER BY position""",
                (task_list.source, task_list.id),
            ).fetchall()
        return [
            Task(id=id, list_id=task_list.id, title=title, completed=bool(done))
            for id, title, done in rows
        ]

    def replace_lists(self, source: str, lists: list[TaskList]) -> None:
        if any(item.source != source for item in lists):
            raise ValueError("List source mismatch")
        ids = [item.id for item in lists]
        with closing(self._connect()) as db:
            with db:
                db.executemany(
                    """INSERT INTO remote_lists (source, id, name) VALUES (?, ?, ?)
                       ON CONFLICT (source, id) DO UPDATE SET name = excluded.name""",
                    [(source, item.id, item.name) for item in lists],
                )
                # Delete missing lists without relying on SQLite's bind-parameter limit.
                previous = db.execute(
                    "SELECT id FROM remote_lists WHERE source = ?", (source,)
                ).fetchall()
                removed = set(row[0] for row in previous) - set(ids)
                db.executemany(
                    "DELETE FROM remote_lists WHERE source = ? AND id = ?",
                    [(source, list_id) for list_id in removed],
                )

    def replace_tasks(self, task_list: TaskList, tasks: list[Task]) -> None:
        if any(task.list_id != task_list.id for task in tasks):
            raise ValueError("Task list mismatch")
        with closing(self._connect()) as db:
            with db:
                db.execute(
                    "DELETE FROM remote_tasks WHERE source = ? AND list_id = ?",
                    (task_list.source, task_list.id),
                )
                db.executemany(
                    """INSERT INTO remote_tasks
                       (source, list_id, id, title, completed, position)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    [
                        (task_list.source, task_list.id, task.id,
                         task.title, int(task.completed), position)
                        for position, task in enumerate(tasks)
                    ],
                )
                db.execute(
                    "INSERT OR IGNORE INTO remote_loaded (source, list_id) VALUES (?, ?)",
                    (task_list.source, task_list.id),
                )

    def add_list(self, task_list: TaskList) -> None:
        with closing(self._connect()) as db:
            with db:
                db.execute(
                    """INSERT INTO remote_lists (source, id, name) VALUES (?, ?, ?)
                       ON CONFLICT (source, id) DO UPDATE SET name = excluded.name""",
                    (task_list.source, task_list.id, task_list.name),
                )
                # A newly created Google list is known to be empty.
                db.execute(
                    "INSERT OR IGNORE INTO remote_loaded (source, list_id) VALUES (?, ?)",
                    (task_list.source, task_list.id),
                )

    def add_task(self, task_list: TaskList, task: Task) -> None:
        with closing(self._connect()) as db:
            with db:
                position = db.execute(
                    """SELECT COALESCE(MAX(position), -1) + 1 FROM remote_tasks
                       WHERE source = ? AND list_id = ?""",
                    (task_list.source, task_list.id),
                ).fetchone()[0]
                db.execute(
                    """INSERT INTO remote_tasks
                       (source, list_id, id, title, completed, position)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT (source, list_id, id) DO UPDATE SET
                           title = excluded.title, completed = excluded.completed""",
                    (task_list.source, task_list.id, task.id, task.title,
                     int(task.completed), position),
                )

    def update_task(self, task_list: TaskList, task: Task) -> None:
        with closing(self._connect()) as db:
            with db:
                db.execute(
                    """UPDATE remote_tasks SET title = ?, completed = ?
                       WHERE source = ? AND list_id = ? AND id = ?""",
                    (task.title, int(task.completed), task_list.source,
                     task_list.id, task.id),
                )

    def clear_source(self, source: str) -> None:
        with closing(self._connect()) as db:
            with db:
                db.execute("DELETE FROM remote_lists WHERE source = ?", (source,))
