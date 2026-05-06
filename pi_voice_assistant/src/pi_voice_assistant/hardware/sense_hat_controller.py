from __future__ import annotations

from dataclasses import dataclass

from pi_voice_assistant.core.state_machine import AssistantState

try:
    from sense_hat import SenseHat
except Exception as exc:  # pragma: no cover
    SenseHat = None
    _SENSE_HAT_IMPORT_ERROR = exc
else:
    _SENSE_HAT_IMPORT_ERROR = None


@dataclass(frozen=True)
class JoystickEvent:
    action: str
    direction: str


class SenseHatController:
    """Handles joystick input and LED matrix state display."""

    _STATE_COLORS = {
        AssistantState.IDLE: (0, 0, 40),
        AssistantState.LISTENING: (0, 80, 0),
        AssistantState.PROCESSING: (80, 80, 0),
        AssistantState.SPEAKING: (80, 0, 80),
        AssistantState.ERROR: (80, 0, 0),
    }

    def __init__(self) -> None:
        if SenseHat is None:
            raise RuntimeError(
                "sense_hat is not available. Install it on the Raspberry Pi first with "
                "`sudo apt install -y sense-hat python3-sense-hat` and then reinstall "
                "the venv requirements if needed."
            ) from _SENSE_HAT_IMPORT_ERROR

        self._sense = SenseHat()
        self._sense.low_light = False

    def get_events(self) -> list[JoystickEvent]:
        return [
            JoystickEvent(action=event.action, direction=event.direction)
            for event in self._sense.stick.get_events()
        ]

    def set_state(self, state: AssistantState) -> None:
        color = self._STATE_COLORS[state]
        self._sense.clear(*color)

    def show_message(self, message: str) -> None:
        self._sense.show_message(message, scroll_speed=0.05)

    def clear(self) -> None:
        self._sense.clear()
