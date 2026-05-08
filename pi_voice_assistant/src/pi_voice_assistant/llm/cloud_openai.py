from __future__ import annotations

from openai import OpenAI

from pi_voice_assistant.utils.config import OpenAIConfig, getenv_required


class CloudOpenAIClient:
    """Sends prompts to the OpenAI API when cloud mode is selected."""

    def __init__(self, config: OpenAIConfig, system_prompt: str) -> None:
        api_key = getenv_required(config.api_key_env)
        self.config = config
        self.system_prompt = system_prompt
        self._client = OpenAI(
            api_key=api_key,
            timeout=config.timeout_seconds,
        )

    def healthcheck(self) -> None:
        getenv_required(self.config.api_key_env)

    def generate_reply(self, prompt: str) -> str:
        response = self._client.responses.create(
            model=self.config.model,
            input=[
                {
                    "role": "system",
                    "content": self.system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )
        return response.output_text.strip()
