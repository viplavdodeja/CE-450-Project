from __future__ import annotations

from pathlib import Path

import soundfile as sf

try:
    import sounddevice as sd
except OSError as exc:  # pragma: no cover
    sd = None
    _SOUNDDEVICE_IMPORT_ERROR = exc
else:
    _SOUNDDEVICE_IMPORT_ERROR = None


class AudioPlayer:
    """Plays generated speech through the configured speaker."""

    def __init__(self, output_device_name: str) -> None:
        _require_sounddevice()
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


def _require_sounddevice() -> None:
    if sd is None:
        raise RuntimeError(
            "sounddevice could not load because PortAudio is missing. "
            "Install it with: sudo apt install -y libportaudio2 portaudio19-dev"
        ) from _SOUNDDEVICE_IMPORT_ERROR
