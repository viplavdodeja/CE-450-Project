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
        device_index = self._find_input_device()
        sample_rate_hz = self._resolve_sample_rate(device_index)
        self._stream = sd.InputStream(
            samplerate=sample_rate_hz,
            channels=self.channels,
            dtype="float32",
            device=device_index,
            callback=self._capture_callback,
        )
        self._stream.start()
        self.sample_rate_hz = sample_rate_hz

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
        available_inputs: list[str] = []
        for index, device in enumerate(sd.query_devices()):
            if device["max_input_channels"] < 1:
                continue
            available_inputs.append(f"{index}: {device['name']}")
            if name_lower in device["name"].lower():
                return index

        raise RuntimeError(
            "Could not find input device matching "
            f"'{self.input_device_name}'. Available input devices: "
            + (", ".join(available_inputs) if available_inputs else "[none]")
        )

    def _resolve_sample_rate(self, device_index: int | None) -> int:
        if device_index is None:
            return self.sample_rate_hz

        device_info = sd.query_devices(device_index)
        try:
            sd.check_input_settings(
                device=device_index,
                samplerate=self.sample_rate_hz,
                channels=self.channels,
                dtype="float32",
            )
            return self.sample_rate_hz
        except Exception:
            default_rate = int(device_info["default_samplerate"])
            print(
                "Configured sample rate "
                f"{self.sample_rate_hz} Hz is not supported by '{device_info['name']}'. "
                f"Falling back to device default {default_rate} Hz."
            )
            return default_rate


def _require_sounddevice() -> None:
    if sd is None:
        raise RuntimeError(
            "sounddevice could not load because PortAudio is missing. "
            "Install it with: sudo apt install -y libportaudio2 portaudio19-dev"
        ) from _SOUNDDEVICE_IMPORT_ERROR
