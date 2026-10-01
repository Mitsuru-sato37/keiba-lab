from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppVersion:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("version must be non-empty")

    def __str__(self) -> str:
        return self.value
