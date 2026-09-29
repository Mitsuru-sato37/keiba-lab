from datetime import UTC, datetime

FIXED_AS_OF = datetime(2022, 1, 1, tzinfo=UTC)
FIXED_POST_TIME = datetime(2022, 1, 1, 6, tzinfo=UTC)
SIMULATION_SEED = 2022010101


def fixture_metadata() -> dict[str, object]:
    return {
        "provider": "FIXTURE",
        "dataset": "BASE-JV",
        "as_of_time": FIXED_AS_OF,
        "simulation_seed": SIMULATION_SEED,
    }
