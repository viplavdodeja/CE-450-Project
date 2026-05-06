from __future__ import annotations

from pathlib import Path

import sounddevice as sd
import soundfile as sf


class AudioPlayer:
    """Plays generated speech through the configured speaker."""

    def __init__(self, output_device_name: str) -> None:
        self.output_device_name = output_device_name

    def play_file(self, path: Path) -> None:
        data, sample_rate = sf.read(path, dtype="float32")
        sd.play(data, sample_rate, device=self._find_output_device())
        sd.wait()

    def _find_output_device(self) -> int | None:
        if not self.output_device_name:
            return None

        name_lower = self.output_device_name.lower()
        for index, device in enumerate(sd.query_devices()):
            if device["max_output_channels"] < 1:
                continue
            if name_lower in device["name"].lower():
                return index

        raise RuntimeError(
            f"Could not find output device matching '{self.output_device_name}'."
        )
