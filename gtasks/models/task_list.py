from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskList:
    id: str
    name: str
    source: str = "local"
