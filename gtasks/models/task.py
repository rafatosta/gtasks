from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Task:
    id: str
    list_id: str
    title: str
    completed: bool = False
    notes: str = ""
    due: str | None = None
    parent: str | None = None
    assigned: bool = False
