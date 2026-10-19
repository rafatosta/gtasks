from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.services.task_service import RemoteSource, TaskService


class TaskController:
    def __init__(self, service: TaskService) -> None:
        self._service = service
        self._selected_list_id: str | None = None
        self._selected_source: str | None = None

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

    def discover_remote(self) -> list[RemoteSource]:
        return self._service.discover_remote()

    def register_remote(self, sources: list[RemoteSource]) -> None:
        self._service.register_remote(sources)

    def remote_accounts(self) -> list[tuple[str, str]]:
        return self._service.remote_accounts()

    def load_remote_lists(self, source: str) -> list[TaskList]:
        return self._service.load_remote_lists(source)

    def cache_remote_lists(self, source: str, lists: list[TaskList]) -> None:
        self._service.cache_remote_lists(source, lists)

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
        task_list = self._service.create_list(name, source)
        if source == "local":
            self.select_list(task_list.id, source)
        return task_list

    def cache_created_remote_list(self, task_list: TaskList) -> None:
        self._service.cache_new_list(task_list)
        self.select_list(task_list.id, task_list.source)

    def get_tasks_for(self, task_list: TaskList) -> list[Task]:
        return self._service.get_tasks(task_list)

    def create_task_for(self, task_list: TaskList, title: str) -> Task:
        return self._service.create_task(task_list, title)

    def set_completed_for(self, task_list: TaskList, task_id: str, completed: bool) -> Task:
        return self._service.set_completed(task_list, task_id, completed)

    def get_tasks(self) -> list[Task]:
        selected = self.selected_list
        return self.get_tasks_for(selected) if selected else []

    def create_task(self, title: str) -> Task:
        selected = self.selected_list
        if selected is None:
            raise ValueError("Select a list first")
        return self.create_task_for(selected, title)

    def set_completed(self, task_id: str, completed: bool) -> Task:
        selected = self.selected_list
        if selected is None:
            raise ValueError("Select a list first")
        return self.set_completed_for(selected, task_id, completed)
