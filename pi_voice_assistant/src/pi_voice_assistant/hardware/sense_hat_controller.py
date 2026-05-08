from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from pi_voice_assistant.core.state_machine import AssistantState

try:
    from sense_hat import SenseHat
except Exception as exc:  # pragma: no cover
    SenseHat = None
    _SENSE_HAT_IMPORT_ERROR = exc
else:
    _SENSE_HAT_IMPORT_ERROR = None


Color = tuple[int, int, int]

OFF: Color = (0, 0, 0)
BLUE: Color = (0, 0, 255)
RED: Color = (255, 0, 0)
ORANGE: Color = (255, 140, 0)
PURPLE: Color = (180, 0, 255)
GREEN: Color = (0, 255, 0)
WHITE: Color = (255, 255, 255)


@dataclass(frozen=True)
class JoystickEvent:
    action: str
    direction: str


def _pixels(rows: list[list[Color]]) -> list[Color]:
    return [pixel for row in rows for pixel in row]


class SenseHatController:
    """Handles joystick input and LED matrix state display."""

    _STATE_PATTERNS = {
        AssistantState.IDLE: _pixels(
            [
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
                [OFF, BLUE, BLUE, OFF, OFF, BLUE, BLUE, OFF],
                [OFF, BLUE, BLUE, OFF, OFF, BLUE, BLUE, OFF],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
                [OFF, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, OFF],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
            ]
        ),
        AssistantState.LISTENING: _pixels(
            [
                [OFF, OFF, OFF, ORANGE, ORANGE, OFF, OFF, OFF],
                [OFF, OFF, ORANGE, ORANGE, ORANGE, ORANGE, OFF, OFF],
                [OFF, OFF, ORANGE, ORANGE, ORANGE, ORANGE, OFF, OFF],
                [OFF, OFF, ORANGE, ORANGE, ORANGE, ORANGE, OFF, OFF],
                [OFF, OFF, OFF, ORANGE, ORANGE, OFF, OFF, OFF],
                [OFF, OFF, OFF, ORANGE, ORANGE, OFF, OFF, OFF],
                [OFF, OFF, ORANGE, ORANGE, ORANGE, ORANGE, OFF, OFF],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
            ]
        ),
        AssistantState.SPEAKING: _pixels(
            [
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
                [OFF, GREEN, GREEN, OFF, OFF, GREEN, GREEN, OFF],
                [OFF, GREEN, GREEN, OFF, OFF, GREEN, GREEN, OFF],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
                [OFF, GREEN, OFF, OFF, OFF, OFF, GREEN, OFF],
                [OFF, OFF, GREEN, GREEN, GREEN, GREEN, OFF, OFF],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
            ]
        ),
        AssistantState.ERROR: _pixels(
            [
                [RED, OFF, OFF, OFF, OFF, OFF, OFF, RED],
                [OFF, RED, OFF, OFF, OFF, OFF, RED, OFF],
                [OFF, OFF, RED, OFF, OFF, RED, OFF, OFF],
                [OFF, OFF, OFF, RED, RED, OFF, OFF, OFF],
                [OFF, OFF, OFF, RED, RED, OFF, OFF, OFF],
                [OFF, OFF, RED, OFF, OFF, RED, OFF, OFF],
                [OFF, RED, OFF, OFF, OFF, OFF, RED, OFF],
                [RED, OFF, OFF, OFF, OFF, OFF, OFF, RED],
            ]
        ),
    }

    _PROCESSING_FRAMES = [
        _pixels(
            [
                [OFF, OFF, OFF, PURPLE, PURPLE, OFF, OFF, OFF],
                [OFF, OFF, OFF, PURPLE, PURPLE, OFF, OFF, OFF],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
                [PURPLE, PURPLE, OFF, OFF, OFF, OFF, PURPLE, PURPLE],
                [PURPLE, PURPLE, OFF, OFF, OFF, OFF, PURPLE, PURPLE],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
                [OFF, OFF, OFF, PURPLE, PURPLE, OFF, OFF, OFF],
                [OFF, OFF, OFF, PURPLE, PURPLE, OFF, OFF, OFF],
            ]
        ),
        _pixels(
            [
                [OFF, OFF, PURPLE, PURPLE, PURPLE, PURPLE, OFF, OFF],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
                [PURPLE, OFF, OFF, OFF, OFF, OFF, OFF, PURPLE],
                [PURPLE, OFF, OFF, OFF, OFF, OFF, OFF, PURPLE],
                [PURPLE, OFF, OFF, OFF, OFF, OFF, OFF, PURPLE],
                [PURPLE, OFF, OFF, OFF, OFF, OFF, OFF, PURPLE],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
                [OFF, OFF, PURPLE, PURPLE, PURPLE, PURPLE, OFF, OFF],
            ]
        ),
        _pixels(
            [
                [OFF, PURPLE, PURPLE, OFF, OFF, PURPLE, PURPLE, OFF],
                [PURPLE, OFF, OFF, PURPLE, PURPLE, OFF, OFF, PURPLE],
                [PURPLE, OFF, OFF, OFF, OFF, OFF, OFF, PURPLE],
                [OFF, PURPLE, OFF, OFF, OFF, OFF, PURPLE, OFF],
                [OFF, PURPLE, OFF, OFF, OFF, OFF, PURPLE, OFF],
                [PURPLE, OFF, OFF, OFF, OFF, OFF, OFF, PURPLE],
                [PURPLE, OFF, OFF, PURPLE, PURPLE, OFF, OFF, PURPLE],
                [OFF, PURPLE, PURPLE, OFF, OFF, PURPLE, PURPLE, OFF],
            ]
        ),
        _pixels(
            [
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
                [OFF, PURPLE, PURPLE, PURPLE, PURPLE, PURPLE, PURPLE, OFF],
                [OFF, PURPLE, OFF, OFF, OFF, OFF, PURPLE, OFF],
                [OFF, PURPLE, OFF, OFF, OFF, OFF, PURPLE, OFF],
                [OFF, PURPLE, OFF, OFF, OFF, OFF, PURPLE, OFF],
                [OFF, PURPLE, OFF, OFF, OFF, OFF, PURPLE, OFF],
                [OFF, PURPLE, PURPLE, PURPLE, PURPLE, PURPLE, PURPLE, OFF],
                [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
            ]
        ),
    ]

    def __init__(self, rotation: int = 180) -> None:
        if SenseHat is None:
            raise RuntimeError(
                "sense_hat is not available. Install it on the Raspberry Pi first with "
                "`sudo apt install -y sense-hat python3-sense-hat` and then reinstall "
                "the venv requirements if needed."
            ) from _SENSE_HAT_IMPORT_ERROR

        self._sense = SenseHat()
        self._sense.low_light = False
        self._sense.set_rotation(rotation % 360)
        self._animation_stop = threading.Event()
        self._animation_thread: threading.Thread | None = None

    def get_events(self) -> list[JoystickEvent]:
        return [
            JoystickEvent(action=event.action, direction=event.direction)
            for event in self._sense.stick.get_events()
        ]

    def set_state(self, state: AssistantState) -> None:
        self._stop_animation()
        if state == AssistantState.PROCESSING:
            self._start_processing_animation()
            return

        pixels = self._STATE_PATTERNS.get(state)
        if pixels is None:
            self._sense.clear()
            return
        self._sense.set_pixels(pixels)

    def show_message(self, message: str) -> None:
        self._stop_animation()
        self._sense.show_message(message, scroll_speed=0.05, text_colour=WHITE)

    def clear(self) -> None:
        self._stop_animation()
        self._sense.clear()

    def _start_processing_animation(self) -> None:
        self._animation_stop.clear()
        self._animation_thread = threading.Thread(
            target=self._run_processing_animation,
            daemon=True,
        )
        self._animation_thread.start()

    def _run_processing_animation(self) -> None:
        frame_index = 0
        while not self._animation_stop.is_set():
            self._sense.set_pixels(self._PROCESSING_FRAMES[frame_index])
            frame_index = (frame_index + 1) % len(self._PROCESSING_FRAMES)
            time.sleep(0.18)

    def _stop_animation(self) -> None:
        if self._animation_thread is None:
            return

        self._animation_stop.set()
        self._animation_thread.join(timeout=0.3)
        self._animation_thread = None
        self._animation_stop.clear()
