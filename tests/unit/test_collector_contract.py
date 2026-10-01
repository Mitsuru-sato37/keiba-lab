import json
from datetime import UTC, datetime

import pytest
from keiba_infrastructure.collector_contract import (
    CollectorImportError,
    batch_from_json,
    batch_to_json,
)
from keiba_infrastructure.fixtures import DeterministicFixtureProvider


def test_collector_contract_round_trips_a_fixture_batch() -> None:
    batch = DeterministicFixtureProvider(seed=7, fixture_version="v1").collect()

    restored = batch_from_json(batch_to_json(batch))

    assert restored == batch
    assert restored.batch_id == "fixture:v1:7"
    assert restored.collected_at.value.tzinfo is UTC


def test_collector_contract_rejects_a_bad_payload_checksum() -> None:
    batch = DeterministicFixtureProvider(seed=7, fixture_version="v1").collect()
    document = json.loads(batch_to_json(batch))
    document["records"][0]["payload"]["value"] = 999

    with pytest.raises(CollectorImportError, match="payload checksum"):
        batch_from_json(json.dumps(document))


def test_collector_contract_rejects_duplicate_record_ids() -> None:
    batch = DeterministicFixtureProvider(seed=7, fixture_version="v1").collect()
    document = json.loads(batch_to_json(batch))
    document["records"][1]["record_id"] = document["records"][0]["record_id"]

    with pytest.raises(CollectorImportError, match="duplicate record_id"):
        batch_from_json(json.dumps(document))


def test_collector_contract_rejects_non_utc_instants() -> None:
    batch = DeterministicFixtureProvider(seed=7, fixture_version="v1").collect()
    document = json.loads(batch_to_json(batch))
    document["collected_at"] = (
        datetime(2022, 1, 1, 9, tzinfo=UTC)
        .isoformat(
            timespec="seconds",
        )
        .replace("+00:00", "+09:00")
    )

    with pytest.raises(CollectorImportError, match="UTC"):
        batch_from_json(json.dumps(document))


def test_collector_contract_rejects_unknown_schema_version() -> None:
    batch = DeterministicFixtureProvider(seed=7, fixture_version="v1").collect()
    document = json.loads(batch_to_json(batch))
    document["schema_version"] = "jra-van-observation-batch/v99"

    with pytest.raises(CollectorImportError, match="schema_version"):
        batch_from_json(json.dumps(document))
