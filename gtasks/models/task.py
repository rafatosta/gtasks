from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Task:
    id: str
    list_id: str
    title: str
    completed: bool = False
