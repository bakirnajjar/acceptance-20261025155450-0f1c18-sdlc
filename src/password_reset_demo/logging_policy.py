"""Redact reset bearer path segments from ordinary Flask and dev-server logs."""

import logging
import re

_TOKEN_PATH = re.compile(r"(/reset/)[^/?\s\"']+")


class _RedactTokenPath(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        record.msg = _TOKEN_PATH.sub(r"\1[redacted]", message)
        record.args = ()
        return True


_REDACTOR = _RedactTokenPath()


def install_token_log_redaction(app_logger: logging.Logger) -> None:
    """Cover Flask exception paths and Werkzeug's local access request line."""
    for logger in (app_logger, logging.getLogger("werkzeug")):
        if _REDACTOR not in logger.filters:
            logger.addFilter(_REDACTOR)
