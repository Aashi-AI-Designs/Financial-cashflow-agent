"""
main.py

Entry point for the financial-cashflow-agent.

This file does one job per module as we build them out:
  - Module 1 (now):  Validates config, sets up logging, confirms environment is ready
  - Module 2 (next): Initialises the database
  - Module 3:        Builds the vector store
  - Module 4:        Registers the tools
  - Module 5:        Starts the agent loop
  - Module 6:        Handles report output

Running this file at the end of each module is how you confirm
the new code integrates cleanly with everything built so far.
"""

import logging
import sys

from config.settings import settings
from config.logging_config import setup_logging


def main() -> None:
    # -------------------------------------------------------------------------
    # Step 1: Set up logging
    # Must happen first — everything else may produce log output
    # -------------------------------------------------------------------------
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_to_file=settings.LOG_TO_FILE,
        log_file_path=settings.LOG_FILE_PATH,
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting financial-cashflow-agent")

    # -------------------------------------------------------------------------
    # Step 2: Validate configuration
    # Fail loudly here rather than silently later deep inside a tool
    # -------------------------------------------------------------------------
    try:
        settings.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Step 3: Display current config (safe — no secrets shown)
    # -------------------------------------------------------------------------
    settings.display()

    # -------------------------------------------------------------------------
    # Step 4: Confirm data directories exist
    # Create them if not — the DB and vector store scripts will need them
    # -------------------------------------------------------------------------
    dirs_to_create = [
        settings.DB_ABSOLUTE_PATH.parent,
        settings.VECTOR_STORE_ABSOLUTE_PATH,
        settings.PDF_DIR,
        settings.PROJECT_ROOT / "logs",
    ]

    for directory in dirs_to_create:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug("Directory ready: %s", directory)

    logger.info("All data directories confirmed")

    # -------------------------------------------------------------------------
    # Module 1 complete — environment is ready
    # Subsequent modules will add their initialisation here
    # -------------------------------------------------------------------------
    logger.info("Environment ready. Modules 2-7 will be wired in as we build them.")
    print("\n✅ Module 1 complete — your environment is set up correctly.\n")


if __name__ == "__main__":
    main()
