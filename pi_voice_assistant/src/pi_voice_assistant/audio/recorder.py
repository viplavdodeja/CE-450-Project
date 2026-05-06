from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf

try:
    import sounddevice as sd
except OSError as exc:  # pragma: no cover
    sd = None
    _SOUNDDEVICE_IMPORT_ERROR = exc
else:
    _SOUNDDEVICE_IMPORT_ERROR = None


@dataclass(frozen=True)
class RecordedAudio:
    path: Path
    duration_seconds: float
    sample_rate_hz: int


class AudioRecorder:
    """Captures microphone input while push-to-talk is active."""

    def __init__(
        self,
        output_dir: Path,
        sample_rate_hz: int,
        channels: int,
        input_device_name: str,
    ) -> None:
        _require_sounddevice()
        self.output_dir = output_dir
        self.sample_rate_hz = sample_rate_hz
        self.channels = channels
        self.input_device_name = input_device_name
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None

    def start(self) -> None:
        if self._stream is not None:
            raise RuntimeError("Audio capture is already active.")

        self._frames = []
        self._stream = sd.InputStream(
            samplerate=self.sample_rate_hz,
            channels=self.channels,
            dtype="float32",
            device=self._find_input_device(),
            callback=self._capture_callback,
        )
        self._stream.start()

    def stop(self) -> RecordedAudio:
        if self._stream is None:
            raise RuntimeError("Audio capture is not active.")

        stream = self._stream
        self._stream = None
        stream.stop()
        stream.close()

        if not self._frames:
            raise RuntimeError("No audio frames were captured.")

        audio = np.concatenate(self._frames, axis=0)
        filename = datetime.now().strftime("capture_%Y%m%d_%H%M%S.wav")
        output_path = self.output_dir / filename
        sf.write(output_path, audio, self.sample_rate_hz)
        duration_seconds = len(audio) / self.sample_rate_hz
        return RecordedAudio(
            path=output_path,
            duration_seconds=duration_seconds,
            sample_rate_hz=self.sample_rate_hz,
        )

    def _capture_callback(
        self, indata: np.ndarray, frames: int, time_info: object, status: sd.CallbackFlags
    ) -> None:
        if status:
            print(f"Audio input status: {status}")
        self._frames.append(indata.copy())

    def _find_input_device(self) -> int | None:
        if not self.input_device_name:
            return None

        name_lower = self.input_device_name.lower()
        for index, device in enumerate(sd.query_devices()):
            if device["max_input_channels"] < 1:
                continue
            if name_lower in device["name"].lower():
                return index

        raise RuntimeError(
            f"Could not find input device matching '{self.input_device_name}'."
        )


def _require_sounddevice() -> None:
    if sd is None:
        raise RuntimeError(
            "sounddevice could not load because PortAudio is missing. "
            "Install it with: sudo apt install -y libportaudio2 portaudio19-dev"
        ) from _SOUNDDEVICE_IMPORT_ERROR
