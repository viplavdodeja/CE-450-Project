from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


@dataclass(frozen=True)
class AppConfig:
    assistant_name: str
    default_mode: str
    max_response_seconds: int
    captured_audio_dir: Path
    logs_dir: Path
    system_prompt: str


@dataclass(frozen=True)
class HardwareConfig:
    joystick_hold_threshold_seconds: float
    input_device_name: str
    output_device_name: str
    sample_rate_hz: int
    channels: int
    poll_interval_seconds: float


@dataclass(frozen=True)
class SttConfig:
    provider: str
    model_path: Path


@dataclass(frozen=True)
class OllamaConfig:
    base_url: str
    model: str
    timeout_seconds: int
    keep_alive: str
    max_tokens: int
    temperature: float


@dataclass(frozen=True)
class TtsConfig:
    provider: str
    enabled: bool
    voice_model_path: Path
    output_wav_path: Path


@dataclass(frozen=True)
class Settings:
    app: AppConfig
    hardware: HardwareConfig
    stt: SttConfig
    ollama: OllamaConfig
    tts: TtsConfig
    config_path: Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_config_path() -> Path:
    root = project_root()
    preferred = root / "config" / "settings.toml"
    if preferred.exists():
        return preferred
    return root / "config" / "settings.example.toml"


def load_settings(config_path: Path | None = None) -> Settings:
    path = config_path or default_config_path()
    raw = _read_toml(path)
    root = project_root()

    settings = Settings(
        app=AppConfig(
            assistant_name=raw["app"]["assistant_name"],
            default_mode=raw["app"].get("default_mode", "local"),
            max_response_seconds=int(raw["app"].get("max_response_seconds", 15)),
            captured_audio_dir=_resolve_path(root, raw["app"]["captured_audio_dir"]),
            logs_dir=_resolve_path(root, raw["app"]["logs_dir"]),
            system_prompt=raw["app"].get(
                "system_prompt",
                "You are a concise Raspberry Pi voice assistant. Keep answers brief and practical.",
            ),
        ),
        hardware=HardwareConfig(
            joystick_hold_threshold_seconds=float(
                raw["hardware"].get("joystick_hold_threshold_seconds", 2.0)
            ),
            input_device_name=raw["hardware"]["input_device_name"],
            output_device_name=raw["hardware"]["output_device_name"],
            sample_rate_hz=int(raw["hardware"].get("sample_rate_hz", 16000)),
            channels=int(raw["hardware"].get("channels", 1)),
            poll_interval_seconds=float(
                raw["hardware"].get("poll_interval_seconds", 0.05)
            ),
        ),
        stt=SttConfig(
            provider=raw["stt"].get("provider", "vosk"),
            model_path=_resolve_path(root, raw["stt"]["model_path"]),
        ),
        ollama=OllamaConfig(
            base_url=raw["ollama"].get("base_url", "http://localhost:11434"),
            model=raw["ollama"]["model"],
            timeout_seconds=int(raw["ollama"].get("timeout_seconds", 60)),
            keep_alive=raw["ollama"].get("keep_alive", "10m"),
            max_tokens=int(raw["ollama"].get("max_tokens", 48)),
            temperature=float(raw["ollama"].get("temperature", 0.2)),
        ),
        tts=TtsConfig(
            provider=raw["tts"].get("provider", "piper"),
            enabled=bool(raw["tts"].get("enabled", False)),
            voice_model_path=_resolve_path(root, raw["tts"]["voice_model_path"]),
            output_wav_path=_resolve_path(root, raw["tts"]["output_wav_path"]),
        ),
        config_path=path,
    )
    ensure_runtime_dirs(settings)
    return settings


def ensure_runtime_dirs(settings: Settings) -> None:
    settings.app.captured_audio_dir.mkdir(parents=True, exist_ok=True)
    settings.app.logs_dir.mkdir(parents=True, exist_ok=True)
    settings.tts.output_wav_path.parent.mkdir(parents=True, exist_ok=True)


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _resolve_path(root: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return root / path
