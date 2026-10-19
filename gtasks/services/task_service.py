from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.repositories.base import TaskDataSource


class TaskService:
    def __init__(self, sources: dict[str, TaskDataSource]) -> None:
        self._sources = sources

    def has_source(self, source: str) -> bool:
        return source in self._sources

    def _repository(self, source: str) -> TaskDataSource:
        if source not in self._sources:
            raise ValueError(f"Data source unavailable: {source}")
        return self._sources[source]

    def get_lists(self) -> list[TaskList]:
        return [
            item
            for repository in self._sources.values()
            for item in repository.list_lists()
        ]

    def create_list(self, name: str, source: str = "local") -> TaskList:
        name = name.strip()
        if not name:
            raise ValueError("List name cannot be empty")
        return self._repository(source).create_list(name)

    def get_tasks(self, task_list: TaskList) -> list[Task]:
        return self._repository(task_list.source).list_tasks(task_list.id)

    def create_task(self, task_list: TaskList, title: str) -> Task:
        title = title.strip()
        if not title:
            raise ValueError("Task title cannot be empty")
        return self._repository(task_list.source).create_task(task_list.id, title)

    def set_completed(self, task_list: TaskList, task_id: str, completed: bool) -> Task:
        return self._repository(task_list.source).set_completed(
            task_list.id, task_id, completed
        )
