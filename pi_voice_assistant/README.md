# Raspberry Pi Voice Assistant

Project scaffold for a Raspberry Pi voice assistant with:

- USB microphone input
- USB speaker output
- Sense HAT joystick push-to-talk
- Sense HAT LED state feedback
- Local LLM via Ollama
- Cloud fallback via OpenAI API
- TTS via Piper

## Suggested layout

- `src/pi_voice_assistant/`: application code
- `config/`: runtime configuration
- `scripts/`: setup and launch helpers for Raspberry Pi
- `systemd/`: service unit for auto-start
- `tests/`: test placeholders
- `logs/`: runtime logs
- `data/`: recordings and generated audio
- `docs/`: notes and hardware setup

## Next steps

1. Install Python dependencies on the Raspberry Pi.
2. Install system tools such as Ollama and Piper.
3. Fill in API keys and model names in `config/settings.example.toml`.
4. Implement each module starting from `src/pi_voice_assistant/main.py`.
