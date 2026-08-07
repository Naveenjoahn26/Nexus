"""
NEXUS EDU — Structured Telemetry Logger.

Provides JSON-formatted structured logging for AI generation events.
Outputs fields like conversation_id, user_id, latency, and model
so they can be ingested by centralized monitoring (e.g., Datadog, ELK).
"""

from __future__ import annotations

import json
import logging
from typing import Any


class TelemetryFormatter(logging.Formatter):
    """Formats log records as JSON with required telemetry fields."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Inject telemetry extras if provided
        for field in [
            "conversation_id",
            "correlation_id",
            "request_id",
            "user_id",
            "latency_ms",
            "model",
            "prompt_version",
            "event",
            "error_type",
            "is_failure",
        ]:
            if hasattr(record, field):
                log_obj[field] = getattr(record, field)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, default=str)


def setup_telemetry_logger() -> logging.Logger:
    """Initialize the global telemetry logger."""
    logger = logging.getLogger("nexus.telemetry")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(TelemetryFormatter())
        logger.addHandler(handler)
        # Prevent propagation to the root logger which might format it as plain text
        logger.propagate = False
        
    return logger

# Singleton telemetry logger instance
telemetry_logger = setup_telemetry_logger()
