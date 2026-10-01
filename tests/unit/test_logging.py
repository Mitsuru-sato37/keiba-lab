import logging
from io import StringIO

from keiba_infrastructure.logging import configure_logging


def test_logging_redacts_configured_secrets() -> None:
    stream = StringIO()
    logger = logging.getLogger("keiba-lab.test")
    configure_logging(stream=stream, secrets=("test-only-secret",))

    logger.warning("credential=%s", "test-only-secret")

    output = stream.getvalue()
    assert "test-only-secret" not in output
    assert "[REDACTED]" in output
