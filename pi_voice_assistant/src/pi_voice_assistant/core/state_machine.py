from enum import Enum


class AssistantState(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"
