from __future__ import annotations

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


class AudioPlayer:
    """Plays generated speech through the configured speaker."""

    def __init__(self, output_device_name: str) -> None:
        _require_sounddevice()
        self.output_device_name = output_device_name

    def play_file(self, path: Path) -> None:
        data, sample_rate = sf.read(path, dtype="float32")
        self.play_array(data, sample_rate)

    def play_array(self, data: np.ndarray, sample_rate: int) -> None:
        device_index = self._find_output_device()
        channels = 1 if data.ndim == 1 else int(data.shape[1])
        output_rate = self._resolve_output_sample_rate(device_index, sample_rate, channels)
        if output_rate != sample_rate:
            data = self._resample_audio(data, sample_rate, output_rate)
            sample_rate = output_rate

        sd.play(data, sample_rate, device=device_index)
        sd.wait()

    def _find_output_device(self) -> int | None:
        if not self.output_device_name:
            return None

        name_lower = self.output_device_name.lower()
        available_outputs: list[str] = []
        for index, device in enumerate(sd.query_devices()):
            if device["max_output_channels"] < 1:
                continue
            available_outputs.append(f"{index}: {device['name']}")
            if name_lower in device["name"].lower():
                return index

        raise RuntimeError(
            "Could not find output device matching "
            f"'{self.output_device_name}'. Available output devices: "
            + (", ".join(available_outputs) if available_outputs else "[none]")
        )

    def _resolve_output_sample_rate(
        self, device_index: int | None, sample_rate_hz: int, channels: int
    ) -> int:
        if device_index is None:
            return sample_rate_hz

        device_info = sd.query_devices(device_index)
        try:
            sd.check_output_settings(
                device=device_index,
                samplerate=sample_rate_hz,
                channels=min(channels, int(device_info["max_output_channels"])),
                dtype="float32",
            )
            return sample_rate_hz
        except Exception:
            default_rate = int(device_info["default_samplerate"])
            print(
                "Playback sample rate "
                f"{sample_rate_hz} Hz is not supported by '{device_info['name']}'. "
                f"Falling back to device default {default_rate} Hz."
            )
            return default_rate

    def _resample_audio(
        self, data: np.ndarray, input_rate_hz: int, output_rate_hz: int
    ) -> np.ndarray:
        if input_rate_hz == output_rate_hz:
            return data

        if data.ndim == 1:
            data = data[:, np.newaxis]

        duration_seconds = data.shape[0] / input_rate_hz
        input_positions = np.linspace(0.0, duration_seconds, num=data.shape[0], endpoint=False)
        output_length = max(1, int(round(duration_seconds * output_rate_hz)))
        output_positions = np.linspace(
            0.0,
            duration_seconds,
            num=output_length,
            endpoint=False,
        )
        resampled_channels = [
            np.interp(output_positions, input_positions, data[:, channel_index])
            for channel_index in range(data.shape[1])
        ]
        resampled = np.stack(resampled_channels, axis=1).astype("float32")
        if resampled.shape[1] == 1:
            return resampled[:, 0]
        return resampled


def _require_sounddevice() -> None:
    if sd is None:
        raise RuntimeError(
            "sounddevice could not load because PortAudio is missing. "
            "Install it with: sudo apt install -y libportaudio2 portaudio19-dev"
        ) from _SOUNDDEVICE_IMPORT_ERROR
