from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

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

        command = [
            "piper",
            "--model",
            str(self.config.voice_model_path),
            "--output_file",
            str(self.config.output_wav_path),
        ]
        subprocess.run(
            command,
            input=text,
            text=True,
            check=True,
        )
        return self.config.output_wav_path
