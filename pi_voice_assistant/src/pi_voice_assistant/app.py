from pi_voice_assistant.core.state_machine import AssistantState


class VoiceAssistantApp:
    def __init__(self) -> None:
        self.state = AssistantState.IDLE

    def run(self) -> None:
        print(f"Starting assistant in state: {self.state.value}")
