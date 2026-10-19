from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.services.task_service import TaskService


class TaskController:
    def __init__(self, service: TaskService) -> None:
        self._service = service
        self._selected_list_id: str | None = None

    @property
    def selected_list(self) -> TaskList | None:
        return next(
            (item for item in self.get_lists() if item.id == self._selected_list_id),
            None,
        )

    def get_lists(self) -> list[TaskList]:
        return self._service.get_lists()

    def select_list(self, list_id: str) -> None:
        if not any(item.id == list_id for item in self.get_lists()):
            raise KeyError(list_id)
        self._selected_list_id = list_id

    def create_list(self, name: str) -> TaskList:
        task_list = self._service.create_list(name)
        self._selected_list_id = task_list.id
        return task_list

    def get_tasks(self) -> list[Task]:
        selected = self.selected_list
        return self._service.get_tasks(selected.id) if selected else []

    def create_task(self, title: str) -> Task:
        selected = self.selected_list
        if selected is None:
            raise ValueError("Select a list first")
        return self._service.create_task(selected.id, title)

    def set_completed(self, task_id: str, completed: bool) -> Task:
        selected = self.selected_list
        if selected is None:
            raise ValueError("Select a list first")
        return self._service.set_completed(selected.id, task_id, completed)
