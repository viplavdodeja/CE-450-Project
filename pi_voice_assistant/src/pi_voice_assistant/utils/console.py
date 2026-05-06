from __future__ import annotations

from pi_voice_assistant.core.state_machine import AssistantState, AssistantStateMachine


class ConsoleReporter:
    def __init__(self, state_machine: AssistantStateMachine) -> None:
        self._state_machine = state_machine

    def state(self, state: AssistantState, detail: str | None = None) -> None:
        descriptor = self._state_machine.descriptor_for(state)
        message = f"STATE {descriptor.emoji} {descriptor.label}"
        if detail:
            message = f"{message} | {detail}"
        print(message)

    def audio(self, detail: str) -> None:
        print(f"AUDIO | {detail}")

    def transcript(self, text: str) -> None:
        print(f"TRANSCRIPT | {text or '[empty]'}")

    def llm_status(self, detail: str) -> None:
        print(f"LLM | {detail}")

    def llm_output(self, text: str) -> None:
        print(f"LLM OUTPUT | {text}")

    def tts_status(self, detail: str) -> None:
        print(f"TTS | {detail}")

    def error(self, detail: str) -> None:
        print(f"ERROR | {detail}")
