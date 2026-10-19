from typing import Protocol

from gtasks.models.task import Task
from gtasks.models.task_list import TaskList


class TaskRepository(Protocol):
    """Operations supported by each storage provider."""

    def list_lists(self) -> list[TaskList]: ...

    def create_list(self, name: str) -> TaskList: ...

    def list_tasks(self, list_id: str) -> list[Task]: ...

    def create_task(self, list_id: str, title: str) -> Task: ...

    def set_completed(self, list_id: str, task_id: str, completed: bool) -> Task: ...
