from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GoogleAccount:
    id: str
    identity: str
    object_path: str

    @property
    def source(self) -> str:
        return f"google:{self.id}"
