from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from pi_voice_assistant.utils.config import TtsConfig


class PiperEngine:
    """Generates spoken responses using Piper."""

    def __init__(self, config: TtsConfig) -> None:
        self.config = config

    def is_available(self) -> bool:
        return (
            self.config.enabled
            and self.config.voice_model_path.exists()
            and shutil.which("piper") is not None
        )

    def synthesize_to_file(self, text: str) -> Path:
        if not self.is_available():
            raise RuntimeError("Piper is not available or is not configured.")

        normalized_text = self._normalize_text(text)
        command = [
            "piper",
            "--model",
            str(self.config.voice_model_path),
            "--output_file",
            str(self.config.output_wav_path),
        ]
        subprocess.run(
            command,
            input=normalized_text,
            text=True,
            check=True,
        )
        self._prepend_leading_silence()
        return self.config.output_wav_path

    def _normalize_text(self, text: str) -> str:
        replacements = {
            "\u2018": "'",
            "\u2019": "'",
            "\u201C": '"',
            "\u201D": '"',
            "\u2013": "-",
            "\u2014": "-",
            "\u2026": "...",
            "\u00A0": " ",
        }
        normalized = text
        for source, target in replacements.items():
            normalized = normalized.replace(source, target)
        return normalized

    def _prepend_leading_silence(self) -> None:
        silence_seconds = self.config.leading_silence_seconds
        if silence_seconds <= 0:
            return

        audio, sample_rate_hz = sf.read(self.config.output_wav_path, dtype="float32")
        if audio.ndim == 1:
            silence = np.zeros(int(sample_rate_hz * silence_seconds), dtype="float32")
        else:
            silence = np.zeros(
                (int(sample_rate_hz * silence_seconds), audio.shape[1]),
                dtype="float32",
            )
        padded_audio = np.concatenate([silence, audio], axis=0)
        sf.write(self.config.output_wav_path, padded_audio, sample_rate_hz)
