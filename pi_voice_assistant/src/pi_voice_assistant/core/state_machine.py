from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import perf_counter


class AssistantState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"

@dataclass(frozen=True)
class StateDescriptor:
    emoji: str
    label: str


STATE_DESCRIPTORS: dict[AssistantState, StateDescriptor] = {
    AssistantState.IDLE: StateDescriptor(emoji="\U0001F610", label="IDLE"),
    AssistantState.LISTENING: StateDescriptor(emoji="\U0001F3A4", label="LISTENING"),
    AssistantState.PROCESSING: StateDescriptor(emoji="\U0001F300", label="PROCESSING"),
    AssistantState.SPEAKING: StateDescriptor(emoji="\U0001F642", label="SPEAKING"),
    AssistantState.ERROR: StateDescriptor(emoji="\u274C", label="ERROR"),
}


@dataclass
class StateSnapshot:
    state: AssistantState
    entered_at: float


class AssistantStateMachine:
    def __init__(self) -> None:
        self._current = StateSnapshot(
            state=AssistantState.IDLE,
            entered_at=perf_counter(),
        )

    @property
    def current(self) -> StateSnapshot:
        return self._current

    def transition_to(self, state: AssistantState) -> StateSnapshot:
        self._current = StateSnapshot(state=state, entered_at=perf_counter())
        return self._current

    def descriptor_for(self, state: AssistantState | None = None) -> StateDescriptor:
        target_state = state or self._current.state
        return STATE_DESCRIPTORS[target_state]
