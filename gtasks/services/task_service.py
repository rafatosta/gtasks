from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.repositories.registry import RemoteSource, RepositoryRegistry


class TaskService:
    """Validates task operations without knowing their storage provider."""

    def __init__(self, repositories: RepositoryRegistry) -> None:
        self._repositories = repositories

    def discover_remote(self) -> list[RemoteSource]:
        return self._repositories.discover_remote()

    def register_remote(self, sources: list[RemoteSource]) -> None:
        self._repositories.register_remote(sources)

    def remote_accounts(self) -> list[tuple[str, str]]:
        return self._repositories.remote_accounts()

    def has_source(self, source: str) -> bool:
        return self._repositories.has_source(source)

    def get_lists(self) -> list[TaskList]:
        return self._repositories.list_lists()

    def load_remote_lists(self, source: str) -> list[TaskList]:
        return self._repositories.load_remote_lists(source)

    def cache_remote_lists(self, source: str, lists: list[TaskList]) -> None:
        self._repositories.cache_remote_lists(source, lists)

    def remember_created_list(self, task_list: TaskList) -> None:
        self._repositories.remember_created(task_list)

    def create_list(self, name: str, source: str = "local") -> TaskList:
        name = name.strip()
        if not name:
            raise ValueError("List name cannot be empty")
        return self._repositories.resolve(source).create_list(name)

    def get_tasks(self, task_list: TaskList) -> list[Task]:
        return self._repositories.resolve(task_list.source).list_tasks(task_list.id)

    def create_task(self, task_list: TaskList, title: str) -> Task:
        title = title.strip()
        if not title:
            raise ValueError("Task title cannot be empty")
        return self._repositories.resolve(task_list.source).create_task(task_list.id, title)

    def set_completed(self, task_list: TaskList, task_id: str, completed: bool) -> Task:
        return self._repositories.resolve(task_list.source).set_completed(
            task_list.id, task_id, completed
        )
