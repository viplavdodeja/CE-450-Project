from __future__ import annotations

import threading

import numpy as np

from pi_voice_assistant.audio.player import AudioPlayer
from pi_voice_assistant.core.state_machine import AssistantState


class StateBeeper:
    _STATE_TONES: dict[AssistantState, list[tuple[float, float]]] = {
        AssistantState.IDLE: [(660.0, 0.05)],
        AssistantState.LISTENING: [(740.0, 0.05)],
        AssistantState.PROCESSING: [(880.0, 0.06)],
        AssistantState.SPEAKING: [(990.0, 0.05)],
        AssistantState.ERROR: [(220.0, 0.10), (180.0, 0.14)],
    }

    def __init__(self, player: AudioPlayer, sample_rate_hz: int = 48000) -> None:
        self._player = player
        self._sample_rate_hz = sample_rate_hz
        self._lock = threading.Lock()

    def play_for_state(self, state: AssistantState) -> None:
        tones = self._STATE_TONES.get(state)
        if not tones:
            return

        thread = threading.Thread(
            target=self._play_tones,
            args=(tones,),
            daemon=True,
        )
        thread.start()

    def _play_tones(self, tones: list[tuple[float, float]]) -> None:
        with self._lock:
            waveform = self._build_waveform(tones)
            self._player.play_array(waveform, self._sample_rate_hz)

    def _build_waveform(self, tones: list[tuple[float, float]]) -> np.ndarray:
        chunks: list[np.ndarray] = []
        for frequency_hz, duration_seconds in tones:
            sample_count = max(1, int(self._sample_rate_hz * duration_seconds))
            timeline = np.linspace(
                0.0,
                duration_seconds,
                sample_count,
                endpoint=False,
            )
            tone = 0.18 * np.sin(2.0 * np.pi * frequency_hz * timeline)
            fade_length = max(1, min(sample_count // 8, int(self._sample_rate_hz * 0.01)))
            fade_in = np.linspace(0.0, 1.0, fade_length)
            fade_out = np.linspace(1.0, 0.0, fade_length)
            tone[:fade_length] *= fade_in
            tone[-fade_length:] *= fade_out
            chunks.append(tone.astype("float32"))
            silence = np.zeros(int(self._sample_rate_hz * 0.03), dtype="float32")
            chunks.append(silence)
        return np.concatenate(chunks) if chunks else np.zeros(1, dtype="float32")
