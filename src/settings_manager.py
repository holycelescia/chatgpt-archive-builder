from pathlib import Path
from typing import Any
import json

from config import REPO_ROOT


SETTINGS_DIR = REPO_ROOT / "settings"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


DEFAULT_CONVERSATION_UI = {
    "background_color": "#212121",
    "text_color": "#ececec",
    "user_bubble_color": "#ab68ff",
    "user_bubble_opacity": "0.12",
    "user_bubble_border_opacity": "0.22",
    "font_size": "16",
    "line_height": "28",
    "conversation_max_width": "1200",
    "user_message_max_width": "850",
    "assistant_message_max_width": "900",
    "image_max_width": "300",
    "user_avatar_enabled": "false",
    "user_avatar_data_uri": "",
    "assistant_avatar_enabled": "false",
    "assistant_avatar_data_uri": "",
}


DEFAULT_SETTINGS = {
    "archive_root": "",
    "template_name": "default",
    "language": "en",
    "conversation_ui": DEFAULT_CONVERSATION_UI,
}


def deep_merge_defaults(defaults: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    merged = defaults.copy()

    for key, value in current.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge_defaults(merged[key], value)
        else:
            merged[key] = value

    return merged


def ensure_settings_file() -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)


def load_settings() -> dict[str, Any]:
    ensure_settings_file()

    try:
        settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        settings = DEFAULT_SETTINGS.copy()
        save_settings(settings)
        return settings

    merged_settings = deep_merge_defaults(DEFAULT_SETTINGS, settings)

    return merged_settings


def save_settings(settings: dict[str, Any]) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_archive_root() -> Path | None:
    settings = load_settings()
    archive_root = settings.get("archive_root", "").strip()

    if not archive_root:
        return None

    return Path(archive_root)


def set_archive_root(path: Path) -> None:
    settings = load_settings()
    settings["archive_root"] = str(path)
    save_settings(settings)


def clear_archive_root() -> None:
    settings = load_settings()
    settings["archive_root"] = ""
    save_settings(settings)


def get_conversation_ui_settings() -> dict[str, str]:
    settings = load_settings()
    return settings["conversation_ui"]


def update_conversation_ui_settings(updates: dict[str, str]) -> dict[str, str]:
    settings = load_settings()

    conversation_ui = settings["conversation_ui"]
    conversation_ui.update(updates)

    save_settings(settings)

    return conversation_ui


def reset_conversation_ui_settings() -> dict[str, str]:
    settings = load_settings()
    settings["conversation_ui"] = DEFAULT_CONVERSATION_UI.copy()
    save_settings(settings)

    return settings["conversation_ui"]