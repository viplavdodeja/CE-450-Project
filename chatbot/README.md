# Sense HAT Terminal Chatbot

This scaffold provides a Raspberry Pi terminal chat interface that:

- reads your prompt from the terminal
- sends it to a local `ollama` server running `qwen2.5:0.5b`
- forces a very short reply
- prints the reply in the terminal
- scrolls the reply across the Sense HAT 8x8 LED matrix

## Files

- `sensehat_chat.py`: main chat application
- `requirements.txt`: Python dependencies

## Expected Pi Setup

This project assumes the Raspberry Pi has:

- Python 3.10+
- a working Sense HAT OS-level install
- `ollama` installed and running locally
- the model `qwen2.5:0.5b` available

## Install

On the Raspberry Pi:

```bash
cd ~/path/to/chatbot
sudo apt update
sudo apt install sense-hat
sudo reboot
```

After reboot:

```bash
cd ~/path/to/chatbot
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If needed:

```bash
ollama pull qwen2.5:0.5b
```

If `ollama serve` prints `bind: address already in use`, Ollama is already running on port `11434`, so you do not need to start it again.

## Run

```bash
python3 sensehat_chat.py
```

Optional flags:

```bash
python3 sensehat_chat.py --model qwen2.5:0.5b --speed 0.06 --text-colour 0,255,255
```

## Use

Type a prompt and press Enter.

- replies are limited to 8 words maximum
- `exit` or `quit` stops the app
- `clear` clears the LED matrix

## Notes

The script tries to keep replies sentence-like by:

- instructing the model to answer in one short sentence
- trimming the final output to at most 8 words
- adding sentence punctuation when missing

The Sense HAT display rotation is adjusted from the accelerometer before each message, so the text orientation tracks how the Pi is positioned.

If the script reports a missing `RTIMU` or `sense_hat` dependency, the Pi is missing the Raspberry Pi OS Sense HAT package. Install it with `sudo apt install sense-hat` and reboot.

If you use a virtual environment, create it with `--system-site-packages`. Otherwise the venv may not see the OS-level `sense_hat` and `RTIMU` modules installed by `apt`.
