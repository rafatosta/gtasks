from collections.abc import Callable

from gtasks.models.task_list import TaskList
from gtasks.repositories.base import TaskRepository

RemoteSource = tuple[str, str, TaskRepository]


class RepositoryRegistry:
    """Resolves data sources and caches the remote list index."""

    def __init__(
        self,
        sources: dict[str, TaskRepository],
        discover_remote: Callable[[], list[RemoteSource]] | None = None,
    ) -> None:
        self._sources = dict(sources)
        self._discover = discover_remote
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
        for source, identity, repository in sources:
            self._sources[source] = repository
            self._accounts[source] = identity

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

    def load_remote_lists(self, source: str) -> list[TaskList]:
        if source == "local":
            raise ValueError("Local lists are not remote")
        return self.resolve(source).list_lists()

    def cache_remote_lists(self, source: str, lists: list[TaskList]) -> None:
        if self.has_source(source):
            self._remote_lists[source] = list(lists)

    def remember_created(self, task_list: TaskList) -> None:
        if task_list.source != "local":
            self._remote_lists.setdefault(task_list.source, []).append(task_list)
