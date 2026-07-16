from enum import Enum, auto


class Mark(Enum):
    MARK100 = auto()   # contract resolves YES
    MARK0 = auto()      # contract resolves NO
    PUSH = auto()        # stake returned, pnl = 0
