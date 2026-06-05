from enum import Enum


class DebugLevel(Enum):
    """Enumerator that allows callers to choose a debug level for their operations"""

    QUIET = 0
    NORMAL = 1
    DEBUG = 2
