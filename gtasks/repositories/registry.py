from collections.abc import Callable

from gtasks.models.task_list import TaskList
from gtasks.repositories.base import TaskRepository
from gtasks.repositories.cache import RemoteTaskCache

RemoteSource = tuple[str, str, TaskRepository]


class RepositoryRegistry:
    """Resolves data sources and caches the remote list index."""

    def __init__(
        self,
        sources: dict[str, TaskRepository],
        discover_remote: Callable[[], list[RemoteSource]] | None = None,
        cache: RemoteTaskCache | None = None,
    ) -> None:
        self._sources = dict(sources)
        self._discover = discover_remote
        self._cache = cache
        self._accounts: dict[str, str] = {}
        self._remote_lists: dict[str, list[TaskList]] = {}

    def discover_remote(self) -> list[RemoteSource]:
        return self._discover() if self._discover else []

    def register_remote(self, sources: list[RemoteSource]) -> None:
        removed = set(self._accounts) - {key for key, _, _ in sources}
        for source in removed:
            self._sources.pop(source, None)
            self._accounts.pop(source, None)
            self._remote_lists.pop(source, None)
            if self._cache is not None:
                self._cache.clear_source(source)
        for source, identity, repository in sources:
            self._sources[source] = repository
            self._accounts[source] = identity
            if source not in self._remote_lists and self._cache is not None:
                self._remote_lists[source] = self._cache.lists(source)

    def remote_accounts(self) -> list[tuple[str, str]]:
        return list(self._accounts.items())

    def has_source(self, source: str) -> bool:
        return source in self._sources

    def resolve(self, source: str) -> TaskRepository:
        try:
            return self._sources[source]
        except KeyError:
            raise ValueError(f"Data source unavailable: {source}") from None

    def list_lists(self) -> list[TaskList]:
        lists = self.resolve("local").list_lists()
        for remote_lists in self._remote_lists.values():
            lists.extend(remote_lists)
        return lists

    def remote_lists(self, source: str) -> list[TaskList]:
        """Read one remote index without accessing the local SQLite connection."""
        return list(self._remote_lists.get(source, []))

    def load_remote_lists(self, source: str) -> list[TaskList]:
        if source == "local":
            raise ValueError("Local lists are not remote")
        return self.resolve(source).list_lists()

    def cache_remote_lists(self, source: str, lists: list[TaskList]) -> None:
        if self.has_source(source):
            if self._cache is not None:
                self._cache.replace_lists(source, lists)
            self._remote_lists[source] = list(lists)

    def remember_created(self, task_list: TaskList) -> None:
        if task_list.source != "local":
            if self._cache is not None:
                self._cache.add_list(task_list)
            self._remote_lists.setdefault(task_list.source, []).append(task_list)

    def cached_tasks(self, task_list: TaskList) -> list | None:
        if task_list.source == "local":
            return self.resolve("local").list_tasks(task_list.id)
        return self._cache.tasks(task_list) if self._cache is not None else None

    def cache_tasks(self, task_list: TaskList, tasks: list) -> None:
        if self._cache is not None and self.has_source(task_list.source):
            self._cache.replace_tasks(task_list, tasks)

    def cache_created_task(self, task_list: TaskList, task) -> None:
        if self._cache is not None:
            self._cache.add_task(task_list, task)

    def cache_updated_task(self, task_list: TaskList, task) -> None:
        if self._cache is not None:
            self._cache.update_task(task_list, task)
