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
    # Module 2: Initialise the database
    # Creates all tables if they don't exist yet (safe to call every startup)
    # -------------------------------------------------------------------------
    from database.db import initialise_database, get_row_counts

    initialise_database()

    counts = get_row_counts()
    total_rows = sum(counts.values())

    if total_rows == 0:
        logger.warning("Database is empty. Run: python database/seed_db.py")
    else:
        logger.info(
            "Database ready — %d rows across %d tables",
            total_rows, len([t for t, c in counts.items() if c > 0])
        )

    # -------------------------------------------------------------------------
    # Module 3: Load the vector store
    # -------------------------------------------------------------------------
    from ingest.vector_store import get_vector_store, VectorStore
    from pathlib import Path

    index_file = settings.VECTOR_STORE_ABSOLUTE_PATH / "index.faiss"
    if not index_file.exists():
        logger.warning(
            "Vector store not found. Run: python ingest/ingest_docs.py"
        )
    else:
        store = get_vector_store()
        stats = store.stats()
        logger.info(
            "Vector store ready — %d chunks, types: %s",
            stats["total_chunks"], ", ".join(stats["business_types"])
        )

    # -------------------------------------------------------------------------
    # Modules 4-7 will be wired in as we build them
    # -------------------------------------------------------------------------
    logger.info("Environment ready.")
    print("\n Environment ready.\n")


if __name__ == "__main__":
    main()
