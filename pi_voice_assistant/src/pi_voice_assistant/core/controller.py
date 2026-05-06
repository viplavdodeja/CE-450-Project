from __future__ import annotations

import time
from pathlib import Path

from pi_voice_assistant.audio.player import AudioPlayer
from pi_voice_assistant.audio.recorder import AudioRecorder, RecordedAudio
from pi_voice_assistant.core.state_machine import AssistantState
from pi_voice_assistant.hardware.sense_hat_controller import SenseHatController
from pi_voice_assistant.llm.local_ollama import LocalOllamaClient
from pi_voice_assistant.stt.transcriber import SpeechTranscriber
from pi_voice_assistant.tts.piper_engine import PiperEngine
from pi_voice_assistant.utils.config import Settings


class AssistantController:
    """Coordinates audio capture, inference, and playback."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.state = AssistantState.IDLE
        self.hardware = SenseHatController()
        self.recorder = AudioRecorder(
            output_dir=settings.app.captured_audio_dir,
            sample_rate_hz=settings.hardware.sample_rate_hz,
            channels=settings.hardware.channels,
            input_device_name=settings.hardware.input_device_name,
        )
        self.transcriber = SpeechTranscriber(settings.stt.model_path)
        self.llm = LocalOllamaClient(
            config=settings.ollama,
            system_prompt=settings.app.system_prompt,
        )
        self.tts = PiperEngine(settings.tts)
        self.player = AudioPlayer(settings.hardware.output_device_name)
        self._press_started_at: float | None = None

    def run_forever(self) -> None:
        self.llm.healthcheck()
        self._set_state(AssistantState.IDLE)
        print("Assistant ready. Press the Sense HAT middle button to talk.")

        try:
            while True:
                try:
                    for event in self.hardware.get_events():
                        self._handle_joystick_event(event.action, event.direction)
                except Exception as exc:
                    self._handle_error(exc)
                time.sleep(self.settings.hardware.poll_interval_seconds)
        finally:
            self.hardware.clear()

    def _handle_joystick_event(self, action: str, direction: str) -> None:
        if direction != "middle":
            return

        if action == "pressed":
            self._press_started_at = time.time()
            self._set_state(AssistantState.LISTENING)
            self.recorder.start()
            print("Listening...")
            return

        if action == "released":
            if self._press_started_at is None:
                return

            press_duration = time.time() - self._press_started_at
            self._press_started_at = None
            capture = self.recorder.stop()
            print(f"Captured {capture.duration_seconds:.2f}s of audio.")
            self._process_capture(capture, press_duration)

    def _process_capture(self, capture: RecordedAudio, press_duration: float) -> None:
        del press_duration
        self._set_state(AssistantState.PROCESSING)

        stt_started_at = time.perf_counter()
        transcript = self.transcriber.transcribe_file(capture.path)
        stt_elapsed = time.perf_counter() - stt_started_at
        print(f"Transcript: {transcript or '[empty]'}")
        print(f"STT latency: {stt_elapsed:.2f}s")
        if not transcript:
            self._set_state(AssistantState.IDLE)
            return

        llm_started_at = time.perf_counter()
        reply = self.llm.generate_reply(transcript)
        llm_elapsed = time.perf_counter() - llm_started_at
        print(f"Assistant: {reply}")
        print(f"LLM latency: {llm_elapsed:.2f}s")

        if self.tts.is_available():
            self._set_state(AssistantState.SPEAKING)
            tts_started_at = time.perf_counter()
            speech_path = self.tts.synthesize_to_file(reply)
            self.player.play_file(speech_path)
            tts_elapsed = time.perf_counter() - tts_started_at
            print(f"TTS + playback latency: {tts_elapsed:.2f}s")
        else:
            print("Piper not configured; skipping spoken playback.")

        self._set_state(AssistantState.IDLE)

    def _set_state(self, state: AssistantState) -> None:
        self.state = state
        self.hardware.set_state(state)

    def _handle_error(self, exc: Exception) -> None:
        self._set_state(AssistantState.ERROR)
        print(f"Error: {exc}")
        time.sleep(1.0)
        self._set_state(AssistantState.IDLE)
