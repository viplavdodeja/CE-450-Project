from __future__ import annotations

from pi_voice_assistant.core.controller import AssistantController
from pi_voice_assistant.llm.cloud_openai import CloudOpenAIClient
from pi_voice_assistant.utils.config import load_settings


class CloudVoiceAssistantApp:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.controller = AssistantController(
            self.settings,
            llm_client=CloudOpenAIClient(
                config=self.settings.openai,
                system_prompt=self.settings.app.system_prompt,
            ),
        )

    def run(self) -> None:
        print(f"Loading config from: {self.settings.config_path}")
        print(
            "Using OpenAI model: "
            f"{self.settings.openai.model} via API"
        )
        self.controller.run_forever()
