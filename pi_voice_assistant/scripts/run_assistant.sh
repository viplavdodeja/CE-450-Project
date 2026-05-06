#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate
export PYTHONPATH="$(pwd)/src"
python -m pi_voice_assistant.main
