# Raspberry Pi Voice Assistant

First working version of a Raspberry Pi voice assistant with:

- USB microphone input
- USB speaker output
- Sense HAT joystick push-to-talk
- Sense HAT LED state feedback
- Local LLM via Ollama
- Local-only Ollama for now
- Optional TTS via Piper

## Suggested layout

- `src/pi_voice_assistant/`: application code
- `config/`: runtime configuration
- `scripts/`: setup and launch helpers for Raspberry Pi
- `systemd/`: service unit for auto-start
- `tests/`: test placeholders
- `logs/`: runtime logs
- `data/`: captured audio and generated audio
- `docs/`: notes and hardware setup

## What works now

- Sense HAT middle-button push-to-talk
- LED color by assistant state
- USB microphone capture to WAV
- Vosk speech-to-text from saved audio
- Local Ollama response generation
- Optional Piper speech playback when enabled

## Raspberry Pi setup

1. Copy this folder to the Pi.
2. From the project root, create the environment and install Python packages:

```bash
bash scripts/setup_pi.sh
```

This installs the required PortAudio system library used by `sounddevice`.

3. Create a real config file:

```bash
cp config/settings.example.toml config/settings.toml
```

4. Edit `config/settings.toml` so these values match your Pi:
- `hardware.input_device_name`
- `hardware.output_device_name`
- `stt.model_path`
- `tts.enabled` and `tts.voice_model_path` if you want spoken output

5. Make sure Ollama is running locally and that `qwen2.5:0.5b` is installed:

```bash
ollama list
curl http://localhost:11434/api/tags
```

6. Download a Vosk model and point `stt.model_path` at it.

## Run

From the project root on the Raspberry Pi:

```bash
bash scripts/run_assistant.sh
```

When it starts:
- the LED should turn blue for idle
- press and hold the Sense HAT middle joystick to speak
- release to transcribe and send the prompt to Ollama
- if Piper is disabled, the reply prints to the terminal

## Notes

- This version is local-only. Cloud mode is not wired in.
- If Piper is not installed, the assistant still works and prints replies.
- Audio captures are saved under `data/audio/`.
