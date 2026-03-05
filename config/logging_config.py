"""
config/logging_config.py

Centralised logging configuration for the entire application.
Call setup_logging() once at startup (in main.py) and every module
that creates its own logger will automatically inherit this config.

Usage in any module:
    import logging
    logger = logging.getLogger(__name__)
    logger.info("This is a log message")

The __name__ convention means each module gets a logger named after
itself (e.g. "tools.sql_tool"), which makes logs easy to trace.
"""

import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_to_file: bool = False, log_file_path: str = "logs/agent.log") -> None:
    """
    Configure logging for the entire application.

    Args:
        log_level: Logging level as string — DEBUG, INFO, WARNING, ERROR
        log_to_file: Whether to also write logs to a file
        log_file_path: Path to the log file (only used if log_to_file=True)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Log format:
    # 2024-01-15 14:32:01 | INFO     | tools.sql_tool | Executing SQL query
    # Timestamp           | Level    | Module name    | Message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Root logger — all other loggers inherit from this
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers to avoid duplicate logs
    # (important when setup_logging is called multiple times in tests)
    root_logger.handlers.clear()

    # --- Console handler (always on) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # --- File handler (optional) ---
    if log_to_file:
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # --- Silence noisy third-party libraries ---
    # These libraries log excessively at DEBUG level and clutter our output
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("faiss").setLevel(logging.WARNING)

    # Confirm logging is ready
    logger = logging.getLogger(__name__)
    logger.debug("Logging initialised at level: %s", log_level.upper())
