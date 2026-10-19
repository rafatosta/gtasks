from dataclasses import replace
from uuid import uuid4

from gtasks.models.task import Task
from gtasks.models.task_list import TaskList


class InMemoryTaskRepository:
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
