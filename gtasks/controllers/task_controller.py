from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.services.task_service import TaskService


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
        item = self._service.create_list(name, source)
        self._selected_list_id = item.id
        self._selected_source = item.source
        return item

    def get_tasks(self) -> list[Task]:
        selected = self.selected_list
        return self._service.get_tasks(selected) if selected else []

    def create_task(self, title: str) -> Task:
        selected = self.selected_list
        if selected is None:
            raise ValueError("Select a list first")
        return self._service.create_task(selected, title)

    def set_completed(self, task_id: str, completed: bool) -> Task:
        selected = self.selected_list
        if selected is None:
            raise ValueError("Select a list first")
        return self._service.set_completed(selected, task_id, completed)
