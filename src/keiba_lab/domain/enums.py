from enum import Enum


class Strategy(str, Enum):
    STABLE = "STABLE"
    BALANCED = "BALANCED"
    LONGSHOT = "LONGSHOT"
    OVERALL = "OVERALL"


class Decision(str, Enum):
    BUY = "BUY"
    SKIP = "SKIP"


class SkipCategory(str, Enum):
    NO_VALUE = "NO_VALUE"
    UNRELIABLE = "UNRELIABLE"
    CAPITAL = "CAPITAL"
    STALE = "STALE"


class DataStatus(str, Enum):
    READY = "READY"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    INVALID = "INVALID"


class BetType(str, Enum):
    WIN = "WIN"
    PLACE = "PLACE"
    QUINELLA = "QUINELLA"
    EXACTA = "EXACTA"
    WIDE = "WIDE"
    TRIO = "TRIO"
    TRIFECTA = "TRIFECTA"
