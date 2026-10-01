import hashlib
import json
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import cast

from keiba_application.ports import ObservationBatch, ObservationRecord
from keiba_domain.time_values import UtcInstant

COLLECTOR_SCHEMA_VERSION = "jra-van-observation-batch/v1"


class CollectorImportError(ValueError):
    """Raised when a collector envelope cannot be imported as one whole batch."""


def _payload_checksum(payload: Mapping[str, object]) -> str:
    serialized = json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _object(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise CollectorImportError(f"{field} must be an object")
    return cast(Mapping[str, object], value)


def _required_string(document: Mapping[str, object], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value:
        raise CollectorImportError(f"{field} must be a non-empty string")
    return value


def _utc_instant(document: Mapping[str, object], field: str) -> UtcInstant:
    value = _required_string(document, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CollectorImportError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise CollectorImportError(f"{field} must be UTC")
    return UtcInstant.from_datetime(parsed)


def batch_to_json(batch: ObservationBatch) -> str:
    records: list[dict[str, object]] = []
    for record in batch.records:
        payload = dict(record.payload)
        item: dict[str, object] = {
            "record_id": record.record_id,
            "provider_record_type": record.provider_record_type,
            "provider_record_key": record.provider_record_key,
            "source_timestamp": record.source_timestamp.value.isoformat(),
            "received_timestamp": record.received_timestamp.value.isoformat(),
            "effective_from": record.effective_from.value.isoformat(),
            "payload": payload,
            "payload_checksum": _payload_checksum(payload),
        }
        if record.effective_to is not None:
            item["effective_to"] = record.effective_to.value.isoformat()
        records.append(item)

    document = {
        "schema_version": COLLECTOR_SCHEMA_VERSION,
        "batch_id": batch.batch_id,
        "provider": batch.provider,
        "provider_version": batch.provider_version,
        "collected_at": batch.collected_at.value.isoformat(),
        "records": records,
    }
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def batch_from_json(payload: str | bytes | Mapping[str, object]) -> ObservationBatch:
    if isinstance(payload, (str, bytes)):
        try:
            decoded: object = json.loads(payload)
        except json.JSONDecodeError as error:
            raise CollectorImportError("collector payload must be valid JSON") from error
    else:
        decoded = payload

    document = _object(decoded, field="collector payload")
    if document.get("schema_version") != COLLECTOR_SCHEMA_VERSION:
        raise CollectorImportError("unsupported schema_version")

    records_value = document.get("records")
    if not isinstance(records_value, list):
        raise CollectorImportError("records must be an array")

    records: list[ObservationRecord] = []
    record_ids: set[str] = set()
    provider = _required_string(document, "provider")
    provider_version = _required_string(document, "provider_version")
    for index, value in enumerate(records_value):
        item = _object(value, field=f"records[{index}]")
        record_id = _required_string(item, "record_id")
        if record_id in record_ids:
            raise CollectorImportError(f"duplicate record_id: {record_id}")
        record_ids.add(record_id)

        payload_value = item.get("payload")
        payload_object = _object(payload_value, field=f"records[{index}].payload")
        checksum = _required_string(item, "payload_checksum")
        if checksum != _payload_checksum(payload_object):
            raise CollectorImportError(f"payload checksum mismatch for {record_id}")

        effective_to_value = item.get("effective_to")
        effective_to = (
            None
            if effective_to_value is None
            else _utc_instant({"effective_to": effective_to_value}, "effective_to")
        )
        records.append(
            ObservationRecord(
                record_id=record_id,
                source=provider,
                source_version=provider_version,
                source_timestamp=_utc_instant(item, "source_timestamp"),
                received_timestamp=_utc_instant(item, "received_timestamp"),
                effective_from=_utc_instant(item, "effective_from"),
                effective_to=effective_to,
                payload=payload_object,
                provider_record_type=_required_string(item, "provider_record_type"),
                provider_record_key=_required_string(item, "provider_record_key"),
            ),
        )

    return ObservationBatch(
        batch_id=_required_string(document, "batch_id"),
        provider=provider,
        provider_version=provider_version,
        collected_at=_utc_instant(document, "collected_at"),
        records=tuple(records),
    )
