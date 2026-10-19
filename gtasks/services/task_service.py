from collections.abc import Callable
from threading import Lock
from datetime import date
from contextlib import ExitStack

from gtasks.i18n import _
from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.repositories.registry import RemoteSource, RepositoryRegistry


class TaskService:
    """Validates task operations without knowing their storage provider."""

    def __init__(self, repositories: RepositoryRegistry) -> None:
        self._repositories = repositories
        self._locks: dict[tuple[str, str], Lock] = {}
        self._locks_guard = Lock()
        self._source_locks: dict[str, Lock] = {}

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
            raise ValueError(_("List name cannot be empty"))
        if source == "local":
            return self._repositories.resolve("local").create_list(name)
        with self._source_lock(source):
            item = self._repositories.resolve(source).create_list(name)
            self._repositories.remember_created(item)
            return item

    def rename_list(self, task_list: TaskList, name: str) -> TaskList:
        name = name.strip()
        if not name:
            raise ValueError(_("List name cannot be empty"))
        with self._source_lock(task_list.source), self._list_lock(task_list):
            updated = self._repositories.resolve(task_list.source).rename_list(task_list.id, name)
            if task_list.source != "local":
                lists = [updated if item.id == task_list.id else item
                         for item in self._repositories.remote_lists(task_list.source)]
                self.cache_remote_lists(task_list.source, lists)
            return updated

    def delete_list(self, task_list: TaskList) -> None:
        with self._source_lock(task_list.source), self._list_lock(task_list):
            if task_list.source != "local":
                # Check the account itself: the cached index may be out of date.
                lists = self.load_remote_lists(task_list.source)
                if len(lists) <= 1:
                    raise ValueError(_("The last list in an account cannot be deleted."))
            self._repositories.resolve(task_list.source).delete_list(task_list.id)
            if task_list.source != "local":
                lists = [item for item in lists if item.id != task_list.id]
                self.cache_remote_lists(task_list.source, lists)

    def cached_tasks(self, task_list: TaskList) -> list[Task] | None:
        return self._repositories.cached_tasks(task_list)

    def _list_lock(self, task_list: TaskList) -> Lock:
        key = (task_list.source, task_list.id)
        with self._locks_guard:
            return self._locks.setdefault(key, Lock())

    def _source_lock(self, source: str) -> Lock:
        with self._locks_guard:
            return self._source_locks.setdefault(source, Lock())

    def sync_source(
        self,
        source: str,
        on_progress: Callable[[TaskList | None], None],
        should_stop: Callable[[], bool] | None = None,
    ) -> None:
        """Refresh complete lists and each task snapshot without blocking GTK."""
        with self._source_lock(source):
            lists = self.load_remote_lists(source)
            self.cache_remote_lists(source, lists)
        on_progress(None)
        first_error = None
        for task_list in lists:
            if should_stop is not None and should_stop():
                return
            try:
                with self._list_lock(task_list):
                    if not any(item.id == task_list.id
                               for item in self._repositories.remote_lists(source)):
                        continue
                    tasks = self.get_tasks(task_list)
                    self._repositories.cache_tasks(task_list, tasks)
            except Exception as error:
                # One unavailable list must not block the others.
                if first_error is None:
                    first_error = error
            else:
                on_progress(task_list)
        if first_error is not None:
            raise first_error

    def get_tasks(self, task_list: TaskList) -> list[Task]:
        return self._repositories.resolve(task_list.source).list_tasks(task_list.id)

    def create_task(self, task_list: TaskList, title: str) -> Task:
        title = self._validate_title(title)
        if task_list.source == "local":
            return self._repositories.resolve("local").create_task(task_list.id, title)
        with self._list_lock(task_list):
            task = self._repositories.resolve(task_list.source).create_task(
                task_list.id, title
            )
            self._repositories.cache_created_task(task_list, task)
            return task

    def set_completed(self, task_list: TaskList, task_id: str, completed: bool) -> Task:
        if task_list.source == "local":
            return self._repositories.resolve("local").set_completed(
                task_list.id, task_id, completed
            )
        with self._list_lock(task_list):
            task = self._repositories.resolve(task_list.source).set_completed(
                task_list.id, task_id, completed
            )
            self._repositories.cache_updated_task(task_list, task)
            return task

    @staticmethod
    def _validate_title(title: str) -> str:
        title = title.strip()
        if not title or len(title) > 1024:
            raise ValueError(_("The title must contain between 1 and 1024 characters."))
        return title

    def update_task(self, task_list: TaskList, task_id: str, title: str,
                    notes: str | None, due: str | None) -> Task:
        title = self._validate_title(title)
        if notes is not None and len(notes) > 8192:
            raise ValueError(_("Details can contain up to 8192 characters."))
        if due is not None:
            try:
                due = date.fromisoformat(due).isoformat()
            except (ValueError, TypeError):
                raise ValueError(_("Choose a valid date.")) from None
        with self._list_lock(task_list):
            updated = self._repositories.resolve(task_list.source).update_task(
                task_list.id, task_id, title, notes, due
            )
            if task_list.source != "local":
                self._repositories.cache_updated_task(task_list, updated)
            return updated

    def delete_task(self, task_list: TaskList, task_id: str) -> None:
        with self._list_lock(task_list):
            self._repositories.resolve(task_list.source).delete_task(task_list.id, task_id)
            if task_list.source != "local":
                self._repositories.cache_deleted_task(task_list, task_id)

    def create_subtask(self, task_list: TaskList, parent: str, title: str) -> Task:
        title = self._validate_title(title)
        with self._list_lock(task_list):
            task = self._repositories.resolve(task_list.source).create_subtask(
                task_list.id, parent, title
            )
            if task_list.source != "local":
                self._repositories.cache_created_task(task_list, task)
            return task

    def move_task(self, task_list: TaskList, task_id: str, destination: TaskList) -> Task:
        if destination.source != task_list.source or destination.id == task_list.id:
            raise ValueError(_("Choose another list from the same account or this device."))
        with self._source_lock(task_list.source), ExitStack() as stack:
            for item in sorted((task_list, destination), key=lambda item: item.id):
                stack.enter_context(self._list_lock(item))
            repository = self._repositories.resolve(task_list.source)
            moved = repository.move_task(task_list.id, task_id, destination.id)
            if task_list.source != "local":
                # A move can change IDs and include subtasks; reload both snapshots.
                for item in (task_list, destination):
                    self._repositories.cache_tasks(item, repository.list_tasks(item.id))
            return moved
