from __future__ import annotations

from pi_voice_assistant.core.controller import AssistantController
from pi_voice_assistant.utils.config import load_settings


class VoiceAssistantApp:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.controller = AssistantController(self.settings)

    def run(self) -> None:
        print(f"Loading config from: {self.settings.config_path}")
        print(
            "Using local Ollama model: "
            f"{self.settings.ollama.model} at {self.settings.ollama.base_url}"
        )
        self.controller.run_forever()
