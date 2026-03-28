"""Centralized logging configuration. Controlled via .env (LOG_ENABLED, LOG_LEVEL)."""

import logging
import sys
from datetime import datetime, timezone

from app.core.config import get_settings

# ── Colors for terminal ──────────────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
GRAY = "\033[90m"

LEVEL_COLORS = {
    "DEBUG": GRAY,
    "INFO": GREEN,
    "WARNING": YELLOW,
    "ERROR": RED,
    "CRITICAL": f"{BOLD}{RED}",
}

# ── Tag colors for log categories ────────────────────────────────────────────
TAG_COLORS = {
    "REQUEST": CYAN,
    "RESPONSE": GREEN,
    "ATS-API": MAGENTA,
    "LINKEDIN-API": BLUE,
    "QUERY": YELLOW,
    "NORMALIZER": WHITE,
    "CLIENT": CYAN,
    "SYNC": MAGENTA,
    "ERROR": RED,
}


class PrettyFormatter(logging.Formatter):
    """Clean, readable log format with colors and aligned tags."""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        level = record.levelname
        level_color = LEVEL_COLORS.get(level, RESET)
        name = record.name.split(".")[-1]  # short module name
        msg = record.getMessage()

        # Extract tag if present: [TAG] message
        tag = ""
        if msg.startswith("[") and "]" in msg:
            tag_end = msg.index("]") + 1
            tag_name = msg[1:tag_end - 1]
            tag_color = TAG_COLORS.get(tag_name, WHITE)
            tag = f" {tag_color}[{tag_name}]{RESET}"
            msg = msg[tag_end:].strip()

        return (
            f"{DIM}{ts}{RESET} "
            f"{level_color}{level:<7}{RESET}"
            f"{tag} "
            f"{GRAY}{name}{RESET} "
            f"{msg}"
        )


class NullHandler(logging.Handler):
    """Swallows all logs when logging is disabled."""

    def emit(self, record: logging.LogRecord) -> None:
        pass


def setup_logging() -> None:
    """Configure logging based on .env settings."""
    settings = get_settings()

    # Root logger for our app
    app_logger = logging.getLogger("app")
    app_logger.handlers.clear()
    app_logger.propagate = False

    if not settings.LOG_ENABLED:
        app_logger.addHandler(NullHandler())
        app_logger.setLevel(logging.CRITICAL + 1)
        return

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    app_logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(PrettyFormatter())
    app_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    for noisy in ["httpx", "httpcore", "asyncio", "sqlalchemy.engine"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    app_logger.info("[REQUEST] Logging initialized | level=%s", settings.LOG_LEVEL)
