import json
import logging

import pytest

from keiba_lab.logging import configure_logging


def test_logging_emits_parseable_structured_record(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO")
    logging.getLogger("keiba_lab.test").info("pipeline ready")
    record = json.loads(capsys.readouterr().err)
    assert record["level"] == "INFO"
    assert record["logger"] == "keiba_lab.test"
    assert record["message"] == "pipeline ready"
    assert record["timestamp"].endswith("Z")
