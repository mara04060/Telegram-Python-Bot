from enum import IntEnum

class State(IntEnum):
    MAIN, RANDOM ,GPT,TALK_SELECT , TALK_DIALOG, QUIZ_SELECT ,QUIZ_DIALOG = range(7)