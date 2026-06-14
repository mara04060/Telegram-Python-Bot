from enum import IntEnum

class State(IntEnum):
    MAIN, RANDOM ,GPT,TALK_SELECT , TALK_DIALOG, QUIZ_SELECT ,QUIZ_DIALOG, VOICE_DIALOG = range(8)