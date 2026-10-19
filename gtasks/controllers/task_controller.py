from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import TypeVar

from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.services.task_service import TaskService

T = TypeVar("T")


class TaskController:
    """Coordinates operations and keeps remote I/O off the GTK thread."""

    def __init__(
        self,
        service: TaskService,
        dispatch: Callable[[Callable[[], None]], object] | None = None,
    ) -> None:
        self._service = service
        self._selected_list_id: str | None = None
        self._selected_source: str | None = None
        self._dispatch = dispatch or (lambda callback: callback())
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._closed = False
        self._syncing: set[str] = set()

    def close(self) -> None:
        self._closed = True
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _run(
        self,
        action: Callable[[], T],
        on_success: Callable[[T], None],
        on_error: Callable[[Exception], None],
        source: str | None = None,
    ) -> None:
        if self._closed:
            return

        def finish(future: Future[T]) -> None:
            if self._closed:
                return
            try:
                result = future.result()
            except Exception as error:
                on_error(error)
            else:
                on_success(result)

        if source == "local":
            future: Future[T] = Future()
            try:
                future.set_result(action())
            except Exception as error:
                future.set_exception(error)
            finish(future)
        else:
            future = self._executor.submit(action)
            future.add_done_callback(lambda done: self._dispatch(lambda: finish(done)))

    @property
    def selected_list(self) -> TaskList | None:
        return next(
            (
                item for item in self.get_lists()
                if item.id == self._selected_list_id
                and item.source == self._selected_source
            ),
            None,
        )

    def has_source(self, source: str) -> bool:
        return self._service.has_source(source)

    def get_lists(self) -> list[TaskList]:
        return self._service.get_lists()

    def select_list(self, list_id: str, source: str = "local") -> None:
        if not any(
            item.id == list_id and item.source == source for item in self.get_lists()
        ):
            raise KeyError((source, list_id))
        self._selected_list_id = list_id
        self._selected_source = source

    def create_list(self, name: str, source: str = "local") -> TaskList:
        """Synchronous operation used by domain tests."""
        task_list = self._service.create_list(name, source)
        self.select_list(task_list.id, source)
        return task_list

    def create_task(self, title: str) -> Task:
        selected = self.selected_list
        if selected is None:
            raise ValueError("Select a list first")
        return self._service.create_task(selected, title)

    def get_tasks(self) -> list[Task]:
        selected = self.selected_list
        return self._service.get_tasks(selected) if selected else []

    def set_completed(self, task_id: str, completed: bool) -> Task:
        selected = self.selected_list
        if selected is None:
            raise ValueError("Select a list first")
        return self._service.set_completed(selected, task_id, completed)

    def discover_remote_async(self, on_success, on_error) -> None:
        def found(sources) -> None:
            self._service.register_remote(sources)
            on_success(self._service.remote_accounts())

        self._run(self._service.discover_remote, found, on_error)

    def load_remote_lists_async(self, source: str, on_success, on_error) -> None:
        def loaded(lists) -> None:
            self._service.cache_remote_lists(source, lists)
            on_success(lists)

        self._run(
            lambda: self._service.load_remote_lists(source),
            loaded, on_error, source=source,
        )

    def create_list_async(self, name: str, source: str, on_success, on_error) -> None:
        def created(task_list: TaskList) -> None:
            self.select_list(task_list.id, task_list.source)
            on_success(task_list)

        self._run(
            lambda: self._service.create_list(name, source),
            created, on_error, source=source,
        )

    def cached_tasks(self, task_list: TaskList) -> list[Task] | None:
        return self._service.cached_tasks(task_list)

    def is_syncing(self, source: str) -> bool:
        return source in self._syncing

    def sync_account_async(
        self, source: str, on_progress, on_done, on_error
    ) -> None:
        # A single full refresh per account; selection never starts a second fetch.
        if source in self._syncing:
            return
        self._syncing.add(source)

        def action() -> None:
            self._service.sync_source(
                source,
                lambda item: self._dispatch(
                    lambda item=item: on_progress(item) if not self._closed else None
                ),
                should_stop=lambda: self._closed,
            )

        def succeeded(_result) -> None:
            self._syncing.discard(source)
            on_done()

        def failed(error: Exception) -> None:
            self._syncing.discard(source)
            on_error(error)

        self._run(action, succeeded, failed, source=source)

    def get_tasks_async(self, task_list: TaskList, on_success, on_error) -> None:
        self._run(
            lambda: self._service.get_tasks(task_list),
            on_success, on_error, source=task_list.source,
        )

    def create_task_async(
        self, task_list: TaskList, title: str, on_success, on_error
    ) -> None:
        self._run(
            lambda: self._service.create_task(task_list, title),
            on_success, on_error, source=task_list.source,
        )

    def set_completed_async(
        self, task_list: TaskList, task_id: str, completed: bool,
        on_success, on_error,
    ) -> None:
        self._run(
            lambda: self._service.set_completed(task_list, task_id, completed),
            on_success, on_error, source=task_list.source,
        )
