from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.repositories.base import TaskListRepository, TaskRepository


class TaskService:
    def __init__(self, lists: TaskListRepository, tasks: TaskRepository) -> None:
        self._lists = lists
        self._tasks = tasks

    def get_lists(self) -> list[TaskList]:
        return self._lists.list_lists()

    def create_list(self, name: str) -> TaskList:
        name = name.strip()
        if not name:
            raise ValueError("List name cannot be empty")
        return self._lists.create_list(name)

    def get_tasks(self, list_id: str) -> list[Task]:
        return self._tasks.list_tasks(list_id)

    def create_task(self, list_id: str, title: str) -> Task:
        title = title.strip()
        if not title:
            raise ValueError("Task title cannot be empty")
        return self._tasks.create_task(list_id, title)

    def set_completed(self, list_id: str, task_id: str, completed: bool) -> Task:
        return self._tasks.set_completed(list_id, task_id, completed)
