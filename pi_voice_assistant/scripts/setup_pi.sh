#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y libportaudio2 portaudio19-dev sense-hat python3-sense-hat

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Install Ollama, Piper, and your STT engine separately."
