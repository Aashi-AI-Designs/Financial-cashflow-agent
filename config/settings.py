"""
config/settings.py

Central configuration for the entire application.
All values are read from environment variables (set in .env).
Nothing is hardcoded here — only defaults are set as fallbacks.

Usage anywhere in the codebase:
    from config.settings import settings
    print(settings.OPENAI_API_KEY)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the project root
# This works regardless of where the script is run from
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


class Settings:
    """
    All configuration lives here.

    Why a class instead of module-level variables?
    - Easy to import as a single object: `from config.settings import settings`
    - Can add validation, type hints, and methods
    - Easy to mock in tests
    """

    # -------------------------------------------------------------------------
    # OpenAI
    # -------------------------------------------------------------------------
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_EMBEDDING_MODEL: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    # Max tokens the LLM is allowed to generate per response
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2048"))

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    DB_PATH: str = os.getenv("DB_PATH", "data/db/runway.db")

    # -------------------------------------------------------------------------
    # Vector Store (FAISS)
    # -------------------------------------------------------------------------
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "data/vector_store/")

    # Number of document chunks to retrieve per RAG query
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))

    # Chunk size and overlap for document splitting (in characters)
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

    # -------------------------------------------------------------------------
    # Agent
    # -------------------------------------------------------------------------
    # Maximum number of ReAct loop iterations before the agent gives up
    AGENT_MAX_ITERATIONS: int = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "false").lower() == "true"
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/agent.log")

    # -------------------------------------------------------------------------
    # Paths (resolved to absolute for safety)
    # -------------------------------------------------------------------------
    @property
    def PROJECT_ROOT(self) -> Path:
        """Absolute path to the project root directory."""
        return Path(__file__).resolve().parent.parent

    @property
    def DB_ABSOLUTE_PATH(self) -> Path:
        return self.PROJECT_ROOT / self.DB_PATH

    @property
    def VECTOR_STORE_ABSOLUTE_PATH(self) -> Path:
        return self.PROJECT_ROOT / self.VECTOR_STORE_PATH

    @property
    def PDF_DIR(self) -> Path:
        return self.PROJECT_ROOT / "data" / "pdfs"

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------
    def validate(self) -> None:
        """
        Call this once at application startup.
        Fails loudly if required config is missing — better to crash early
        with a clear message than fail silently deep inside the application.
        """
        errors = []

        if not self.OPENAI_API_KEY:
            errors.append(
                "OPENAI_API_KEY is not set. Add it to your .env file."
            )

        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            errors.append(
                f"CHUNK_OVERLAP ({self.CHUNK_OVERLAP}) must be less than "
                f"CHUNK_SIZE ({self.CHUNK_SIZE})."
            )

        if self.AGENT_MAX_ITERATIONS < 1:
            errors.append("AGENT_MAX_ITERATIONS must be at least 1.")

        if errors:
            raise ValueError(
                "Configuration errors found:\n" + "\n".join(f"  - {e}" for e in errors)
            )

    def display(self) -> None:
        """
        Print a safe summary of current config (no secrets).
        Useful for debugging and confirming the right .env is loaded.
        """
        print("\n=== financial-cashflow-agent configuration ===")
        print(f"  OpenAI Model     : {self.OPENAI_CHAT_MODEL}")
        print(f"  Embedding Model  : {self.OPENAI_EMBEDDING_MODEL}")
        print(f"  Max Tokens       : {self.OPENAI_MAX_TOKENS}")
        print(f"  DB Path          : {self.DB_ABSOLUTE_PATH}")
        print(f"  Vector Store     : {self.VECTOR_STORE_ABSOLUTE_PATH}")
        print(f"  RAG Top K        : {self.RAG_TOP_K}")
        print(f"  Chunk Size       : {self.CHUNK_SIZE}")
        print(f"  Chunk Overlap    : {self.CHUNK_OVERLAP}")
        print(f"  Agent Max Iter   : {self.AGENT_MAX_ITERATIONS}")
        print(f"  Log Level        : {self.LOG_LEVEL}")
        print(f"  Log To File      : {self.LOG_TO_FILE}")
        print(f"  API Key Set      : {'YES' if self.OPENAI_API_KEY else 'NO ❌'}")
        print("=" * 46 + "\n")


# Single shared instance — import this everywhere
settings = Settings()
