from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from typing import List, Tuple

import requests
from sense_hat import SenseHat


SYSTEM_PROMPT = (
    "Reply with exactly one short, complete sentence. "
    "Keep it under 8 words whenever possible. "
    "Directly answer the user's prompt. "
    "Be dry, sarcastic, and useful. "
    "No greetings, no disclaimers, no follow-up questions, no lists."
)

BORING_PATTERNS = (
    re.compile(r"^hello[!,. ]*(how can i assist you today\??)?$", re.IGNORECASE),
    re.compile(r"^i'?m not hungry.*$", re.IGNORECASE),
    re.compile(r"^eat well-balanced meals.*$", re.IGNORECASE),
    re.compile(r"^i'?m not needed.*$", re.IGNORECASE),
)

SARCASTIC_FALLBACKS = {
    "hello": "Hello, clearly this is urgent.",
    "hi": "Hi, a monumental occasion.",
    "hey": "Hey, thrilling start.",
    "im hungry": "Eat something edible, obviously.",
    "i'm hungry": "Eat something edible, obviously.",
    "what should i eat?": "Tacos, unless disappointment sounds tastier.",
    "what should i eat": "Tacos, unless disappointment sounds tastier.",
    "no": "Convincing argument, truly airtight.",
}

EXIT_WORDS = {"exit", "quit"}

@dataclass
class AppConfig:
    model: str
    ollama_url: str
    scroll_speed: float
    text_colour: Tuple[int, int, int]
    background_colour: Tuple[int, int, int]


def parse_rgb(value: str) -> Tuple[int, int, int]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("RGB values must look like 255,255,255")

    try:
        red, green, blue = (int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("RGB values must be integers") from exc

    if any(channel < 0 or channel > 255 for channel in (red, green, blue)):
        raise argparse.ArgumentTypeError("RGB values must be between 0 and 255")

    return red, green, blue


def parse_args() -> AppConfig:
    parser = argparse.ArgumentParser(
        description="Terminal chat interface for Ollama + Sense HAT"
    )
    parser.add_argument("--model", default="chatmodel")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434/api/chat")
    parser.add_argument("--speed", type=float, default=0.07)
    parser.add_argument("--text-colour", type=parse_rgb, default=(0, 255, 255))
    parser.add_argument("--background-colour", type=parse_rgb, default=(0, 0, 0))
    args = parser.parse_args()

    return AppConfig(
        model=args.model,
        ollama_url=args.ollama_url,
        scroll_speed=args.speed,
        text_colour=args.text_colour,
        background_colour=args.background_colour,
    )


def request_llm_reply(
    config: AppConfig, history: List[dict[str, str]], user_text: str
) -> str:
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": user_text.strip()},
        ],
        "stream": False,
        "options": {
            "temperature": 0.8,
            "top_p": 0.9,
            "repeat_penalty": 1.15,
            "num_predict": 20,
        },
    }

    response = requests.post(config.ollama_url, json=payload, timeout=60)
    response.raise_for_status()
    body = response.json()
    raw_reply = body.get("message", {}).get("content", "").strip()
    if not raw_reply:
        return "I have no reply."
    return raw_reply


def fallback_reply(user_text: str) -> str:
    lowered = re.sub(r"\s+", " ", user_text.strip().lower())
    return SARCASTIC_FALLBACKS.get(lowered, "Sure, that sounds brilliantly thought out.")


def is_boring_reply(reply: str) -> bool:
    clean = reply.strip()
    return any(pattern.match(clean) for pattern in BORING_PATTERNS)


def normalize_reply(reply: str) -> str:
    clean = re.sub(r"\s+", " ", reply.strip())
    clean = re.sub(r"^[\"'`]+|[\"'`]+$", "", clean)

    words = clean.split()
    if not words:
        return "I have no reply."

    trimmed = " ".join(words[:8])
    trimmed = trimmed.rstrip(" ,;:")

    if trimmed[-1] not in ".!?":
        trimmed += "."

    return trimmed


def set_rotation_from_orientation(sense: SenseHat) -> None:
    accel = sense.get_accelerometer_raw()
    x_axis = accel.get("x", 0.0)
    y_axis = accel.get("y", 0.0)

    if abs(x_axis) > abs(y_axis):
        rotation = 90 if x_axis < 0 else 270
    else:
        rotation = 0 if y_axis > 0 else 180

    sense.set_rotation(rotation)


def show_on_sensehat(sense: SenseHat, config: AppConfig, message: str) -> None:
    set_rotation_from_orientation(sense)
    sense.show_message(
        message,
        scroll_speed=config.scroll_speed,
        text_colour=config.text_colour,
        back_colour=config.background_colour,
    )


def print_banner(config: AppConfig) -> None:
    print("Sense HAT Chat")
    print(f"Model: {config.model}")
    print("Type a question, then press Enter.")
    print("Commands: clear, exit, quit")


def run_chat() -> int:
    config = parse_args()
    sense = SenseHat()
    history: List[dict[str, str]] = []
    sense.clear(*config.background_colour)
    print_banner(config)

    while True:
        try:
            user_text = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_text:
            continue

        lowered = user_text.lower()
        if lowered in EXIT_WORDS:
            print("Assistant> Goodbye.")
            break

        if lowered == "clear":
            sense.clear(*config.background_colour)
            history.clear()
            print("Assistant> Display cleared.")
            continue

        try:
            raw_reply = request_llm_reply(config, history, user_text)
            if is_boring_reply(raw_reply):
                raw_reply = fallback_reply(user_text)
            final_reply = normalize_reply(raw_reply)
        except requests.RequestException as exc:
            final_reply = "Ollama is unavailable."
            print(f"Assistant> {final_reply}")
            print(f"Error: {exc}", file=sys.stderr)
            show_on_sensehat(sense, config, final_reply)
            continue
        except Exception as exc:  # Defensive guard for sensor/runtime issues.
            final_reply = "Something went wrong."
            print(f"Assistant> {final_reply}")
            print(f"Error: {exc}", file=sys.stderr)
            show_on_sensehat(sense, config, final_reply)
            continue

        history.extend(
            [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": final_reply},
            ]
        )
        if len(history) > 8:
            history = history[-8:]

        print(f"Assistant> {final_reply}")
        show_on_sensehat(sense, config, final_reply)

    sense.clear(*config.background_colour)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_chat())
