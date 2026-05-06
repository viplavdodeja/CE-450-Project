from __future__ import annotations

import json
import wave
from pathlib import Path

try:
    from vosk import KaldiRecognizer, Model
except ModuleNotFoundError:  # pragma: no cover
    KaldiRecognizer = None
    Model = None


class SpeechTranscriber:
    """Converts recorded audio into text."""

    def __init__(self, model_path: Path) -> None:
        if Model is None or KaldiRecognizer is None:
            raise RuntimeError("vosk is not installed. Add it to the Pi environment.")
        if not model_path.exists():
            raise RuntimeError(f"Vosk model path does not exist: {model_path}")

        self._model = Model(str(model_path))

    def transcribe_file(self, audio_path: Path) -> str:
        with wave.open(str(audio_path), "rb") as wav_file:
            recognizer = KaldiRecognizer(self._model, wav_file.getframerate())
            recognizer.SetWords(True)

            while True:
                chunk = wav_file.readframes(4000)
                if not chunk:
                    break
                recognizer.AcceptWaveform(chunk)

            final_result = json.loads(recognizer.FinalResult())
            return str(final_result.get("text", "")).strip()
