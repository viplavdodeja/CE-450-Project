from __future__ import annotations

import requests

from pi_voice_assistant.utils.config import OllamaConfig


class LocalOllamaClient:
    """Sends prompts to the local Ollama runtime."""

    def __init__(self, config: OllamaConfig, system_prompt: str) -> None:
        self.config = config
        self.system_prompt = system_prompt

    def healthcheck(self) -> None:
        response = requests.get(
            f"{self.config.base_url}/api/tags",
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()

    def generate_reply(self, prompt: str) -> str:
        payload = {
            "model": self.config.model,
            "prompt": self._build_prompt(prompt),
            "stream": False,
            "keep_alive": self.config.keep_alive,
            "options": {
                "num_predict": self.config.max_tokens,
                "temperature": self.config.temperature,
            },
        }
        response = requests.post(
            f"{self.config.base_url}/api/generate",
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return str(data.get("response", "")).strip()

    def _build_prompt(self, user_prompt: str) -> str:
        return (
            f"System: {self.system_prompt}\n"
            f"User: {user_prompt}\n"
            "Assistant:"
        )
