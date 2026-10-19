from dataclasses import replace
from uuid import uuid4

from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.repositories.base import TaskRepository


class InMemoryTaskRepository(TaskRepository):
    """Temporary adapter: data exists only while the application is running."""

    def __init__(self, source: str = "local") -> None:
        self._source = source
        self._lists: dict[str, TaskList] = {}
        self._tasks: dict[str, list[Task]] = {}

    def list_lists(self) -> list[TaskList]:
        return list(self._lists.values())

    def create_list(self, name: str) -> TaskList:
        task_list = TaskList(id=str(uuid4()), name=name, source=self._source)
        self._lists[task_list.id] = task_list
        self._tasks[task_list.id] = []
        return task_list

    def rename_list(self, list_id: str, name: str) -> TaskList:
        item = replace(self._lists[list_id], name=name)
        self._lists[list_id] = item
        return item

    def delete_list(self, list_id: str) -> None:
        del self._lists[list_id]
        del self._tasks[list_id]

    def list_tasks(self, list_id: str) -> list[Task]:
        return list(self._tasks[list_id])

    def create_task(self, list_id: str, title: str) -> Task:
        task = Task(id=str(uuid4()), list_id=list_id, title=title)
        self._tasks[list_id].append(task)
        return task

    def set_completed(self, list_id: str, task_id: str, completed: bool) -> Task:
        tasks = self._tasks[list_id]
        for index, task in enumerate(tasks):
            if task.id == task_id:
                updated = replace(task, completed=completed)
                tasks[index] = updated
                return updated
        raise KeyError(task_id)

    def update_task(self, list_id: str, task_id: str, title: str,
                    notes: str | None, due: str | None) -> Task:
        tasks = self._tasks[list_id]
        for index, task in enumerate(tasks):
            if task.id == task_id:
                updated = replace(task, title=title, notes=task.notes if notes is None else notes, due=due)
                tasks[index] = updated
                return updated
        raise KeyError(task_id)

    def _subtree(self, list_id, task_id) -> set[str]:
        tasks = self._tasks[list_id]
        if not any(task.id == task_id for task in tasks):
            raise KeyError(task_id)
        ids = {task_id}
        while True:
            expanded = ids | {task.id for task in tasks if task.parent in ids}
            if expanded == ids:
                return ids
            ids = expanded

    def delete_task(self, list_id: str, task_id: str) -> None:
        ids = self._subtree(list_id, task_id)
        self._tasks[list_id] = [task for task in self._tasks[list_id] if task.id not in ids]

    def create_subtask(self, list_id: str, parent: str, title: str) -> Task:
        self._subtree(list_id, parent)
        task = replace(self.create_task(list_id, title), parent=parent)
        self._tasks[list_id][-1] = task
        return task

    def move_task(self, list_id: str, task_id: str, destination: str) -> Task:
        target = self._tasks[destination]
        ids = self._subtree(list_id, task_id)
        moved = [replace(task, list_id=destination,
                         parent=None if task.id == task_id else task.parent)
                 for task in self._tasks[list_id] if task.id in ids]
        self._tasks[list_id] = [task for task in self._tasks[list_id] if task.id not in ids]
        target.extend(moved)
        return next(task for task in moved if task.id == task_id)
