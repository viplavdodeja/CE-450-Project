from __future__ import annotations

import time
from pathlib import Path

from pi_voice_assistant.audio.beeper import StateBeeper
from pi_voice_assistant.audio.player import AudioPlayer
from pi_voice_assistant.audio.recorder import AudioRecorder, RecordedAudio
from pi_voice_assistant.core.state_machine import AssistantState, AssistantStateMachine
from pi_voice_assistant.hardware.sense_hat_controller import SenseHatController
from pi_voice_assistant.llm.local_ollama import LocalOllamaClient
from pi_voice_assistant.stt.transcriber import SpeechTranscriber
from pi_voice_assistant.tts.piper_engine import PiperEngine
from pi_voice_assistant.utils.console import ConsoleReporter
from pi_voice_assistant.utils.config import Settings


class AssistantController:
    """Coordinates audio capture, inference, and playback."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.state_machine = AssistantStateMachine()
        self.reporter = ConsoleReporter(self.state_machine)
        self.hardware = SenseHatController()
        self.player = AudioPlayer(settings.hardware.output_device_name)
        self.beeper = StateBeeper(self.player)
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
        self._press_started_at: float | None = None

    def run_forever(self) -> None:
        try:
            self.llm.healthcheck()
        except Exception as exc:
            self._handle_error(exc)
        self._set_state(AssistantState.IDLE, detail="Assistant ready. Press the Sense HAT middle button to talk.")

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
            self.recorder.start()
            self._press_started_at = time.time()
            self._set_state(AssistantState.LISTENING, detail="Push-to-talk active")
            return

        if action == "released":
            if self._press_started_at is None:
                return

            press_duration = time.time() - self._press_started_at
            self._press_started_at = None
            capture = self.recorder.stop()
            self.reporter.audio(
                f"captured {capture.duration_seconds:.2f}s at {capture.sample_rate_hz} Hz"
            )
            self._process_capture(capture, press_duration)

    def _process_capture(self, capture: RecordedAudio, press_duration: float) -> None:
        del press_duration
        self._set_state(AssistantState.PROCESSING, detail="Running STT, LLM, and TTS")

        stt_started_at = time.perf_counter()
        transcript = self.transcriber.transcribe_file(capture.path)
        stt_elapsed = time.perf_counter() - stt_started_at
        self.reporter.transcript(transcript)
        self.reporter.audio(f"stt latency {stt_elapsed:.2f}s")
        if not transcript:
            self._set_state(AssistantState.IDLE, detail="No speech recognized")
            return

        self.reporter.llm_status("generating response")
        llm_started_at = time.perf_counter()
        reply = self.llm.generate_reply(transcript)
        llm_elapsed = time.perf_counter() - llm_started_at
        self.reporter.llm_output(reply)
        self.reporter.llm_status(f"completed in {llm_elapsed:.2f}s")

        if self.tts.is_available():
            tts_started_at = time.perf_counter()
            self.reporter.tts_status("synthesizing audio")
            speech_path = self.tts.synthesize_to_file(reply)
            tts_elapsed = time.perf_counter() - tts_started_at
            self.reporter.tts_status(f"synthesized in {tts_elapsed:.2f}s")
            self._set_state(AssistantState.SPEAKING, detail="Playing response")
            self.player.play_file(speech_path)
        else:
            self.reporter.tts_status("disabled; terminal output only")

        self._set_state(AssistantState.IDLE, detail="Ready")

    def _set_state(self, state: AssistantState, detail: str | None = None) -> None:
        self.state_machine.transition_to(state)
        self.hardware.set_state(state)
        self.reporter.state(state, detail=detail)
        if self.settings.hardware.state_beeps_enabled:
            self.beeper.play_for_state(state)

    def _handle_error(self, exc: Exception) -> None:
        self._press_started_at = None
        self._set_state(AssistantState.ERROR, detail="Failure detected")
        self.reporter.error(str(exc))
        time.sleep(self.settings.app.error_hold_seconds)
        self._set_state(AssistantState.IDLE, detail="Recovered from error")
