# config package
# Exposes settings and logging setup at the package level
# so any module can do: from config import settings

from config.settings import settings
from config.logging_config import setup_logging

__all__ = ["settings", "setup_logging"]
