from collections.abc import Callable

from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.repositories.base import TaskDataSource

RemoteSource = tuple[str, str, TaskDataSource]


class TaskService:
    def __init__(
        self,
        sources: dict[str, TaskDataSource],
        discover_remote: Callable[[], list[RemoteSource]] | None = None,
    ) -> None:
        self._sources = dict(sources)
        self._discover_remote = discover_remote
        self._remote_names: dict[str, str] = {}
        self._remote_lists: dict[str, list[TaskList]] = {}

    def discover_remote(self) -> list[RemoteSource]:
        return self._discover_remote() if self._discover_remote else []

    def register_remote(self, sources: list[RemoteSource]) -> None:
        current = {name for name in self._sources if name != "local"}
        discovered = {key for key, _, _ in sources}
        for removed in current - discovered:
            self._sources.pop(removed)
            self._remote_names.pop(removed, None)
            self._remote_lists.pop(removed, None)
        for key, name, repository in sources:
            self._sources[key] = repository
            self._remote_names[key] = name

    def remote_accounts(self) -> list[tuple[str, str]]:
        return list(self._remote_names.items())

    def has_source(self, source: str) -> bool:
        return source in self._sources

    def _repository(self, source: str) -> TaskDataSource:
        if source not in self._sources:
            raise ValueError(f"Data source unavailable: {source}")
        return self._sources[source]

    def get_lists(self) -> list[TaskList]:
        lists = self._sources["local"].list_lists()
        for cached in self._remote_lists.values():
            lists.extend(cached)
        return lists

    def load_remote_lists(self, source: str) -> list[TaskList]:
        if source == "local":
            raise ValueError("Local lists are not remote")
        return self._repository(source).list_lists()

    def cache_remote_lists(self, source: str, lists: list[TaskList]) -> None:
        self._remote_lists[source] = lists

    def cache_new_list(self, item: TaskList) -> None:
        if item.source != "local":
            self._remote_lists.setdefault(item.source, []).append(item)

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
