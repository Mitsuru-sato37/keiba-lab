import logging
import re
import sys
from collections.abc import Iterable
from typing import TextIO


class _RedactionFilter(logging.Filter):
    def __init__(self, secrets: Iterable[str]) -> None:
        super().__init__()
        self._secrets = tuple(secret for secret in secrets if secret)

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for secret in self._secrets:
            message = re.sub(re.escape(secret), "[REDACTED]", message)
        record.msg = message
        record.args = ()
        return True


def configure_logging(
    *,
    stream: TextIO | None = None,
    secrets: Iterable[str] = (),
) -> None:
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.addFilter(_RedactionFilter(secrets))
    handler.setFormatter(logging.Formatter("%(asctime)sZ %(levelname)s %(name)s %(message)s"))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
