from enum import Enum


class MODE(Enum):
    DEFAULT = 0
    BUY = 1
    SELL = 2


class STATE(Enum):
    START = 0
    PROCESS = 1
    END = 2
