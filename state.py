from enum import IntEnum

class State(IntEnum):
    MAIN = 0
    RANDOM = 1
    GPT = 2
    TALK_SELECT = 3
    TALK_DIALOG = 4
    QUIZ_SELECT = 5
    QUIZ_DIALOG = 6