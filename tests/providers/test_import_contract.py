from datetime import UTC, datetime

import pytest

from keiba_lab.providers.import_contract import ImportBatch, ImportBatchStore, ImportRecord


def batch(payload: str = "race-1") -> ImportBatch:
    return ImportBatch(
        provider="FIXTURE",
        contract_version="BASE-JV:v1",
        batch_id="B1",
        received_at=datetime(2022, 1, 1, tzinfo=UTC),
        records=(ImportRecord(provider_key="R1", payload=payload, checksum=f"sha:{payload}"),),
    )


def test_import_batch_promotion_is_idempotent_and_preserves_records() -> None:
    store = ImportBatchStore()
    store.stage(batch())
    assert store.promote("B1") is True
    assert store.promote("B1") is False
    assert store.eligible("B1")[0].payload == "race-1"


def test_import_batch_rejects_changed_duplicate_and_failed_batches() -> None:
    store = ImportBatchStore()
    store.stage(batch())
    with pytest.raises(ValueError, match="immutable"):
        store.stage(batch("changed"))
    store.stage(batch("other").model_copy(update={"batch_id": "B2"}))
    store.fail("B2", "parse error")
    assert store.eligible("B2") == ()
