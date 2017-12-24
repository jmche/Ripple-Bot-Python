from enum import Enum, auto


class MODE(Enum):
    BUY = auto()
    SELL = auto()
    DEFAULT = auto()


class STATE(Enum):
    START = auto()
    PROCESS = auto()
    END = auto()
