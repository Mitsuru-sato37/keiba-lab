from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

JRA_TIMEZONE = ZoneInfo("Asia/Tokyo")


@dataclass(frozen=True, slots=True)
class UtcInstant:
    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None or self.value.utcoffset() is None:
            raise ValueError("instant must be timezone-aware")
        object.__setattr__(self, "value", self.value.astimezone(UTC))

    @classmethod
    def from_datetime(cls, value: datetime) -> "UtcInstant":
        return cls(value)

    def to_tokyo(self) -> datetime:
        return self.value.astimezone(JRA_TIMEZONE)
