from pathlib import Path
import re
import base64
import mimetypes

from settings_manager import (
    SETTINGS_DIR,
    DEFAULT_CONVERSATION_UI,
    get_conversation_ui_settings,
    update_conversation_ui_settings,
    reset_conversation_ui_settings,
)


PATCH_START = "<!-- ARCHIVER-CONVERSATION-UI-START -->"
PATCH_END = "<!-- ARCHIVER-CONVERSATION-UI-END -->"

GENERATED_PATCH_FILE = SETTINGS_DIR / "generated_conversation_ui_patch.html"


HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


def validate_hex_color(value: str, setting_name: str) -> str:
    cleaned = value.strip()

    if not HEX_COLOR_PATTERN.match(cleaned):
        raise ValueError(f"{setting_name} must be a hex color like #ab68ff.")

    return cleaned


def validate_number(value: str, setting_name: str, minimum: float, maximum: float) -> str:
    cleaned = str(value).strip()

    try:
        number = float(cleaned)
    except ValueError as error:
        raise ValueError(f"{setting_name} must be a number.") from error

    if number < minimum or number > maximum:
        raise ValueError(f"{setting_name} must be between {minimum} and {maximum}.")

    if number.is_integer():
        return str(int(number))

    return str(number)


def hex_to_rgba(hex_color: str, opacity: str) -> str:
    hex_color = validate_hex_color(hex_color, "Color")
    opacity_value = float(validate_number(opacity, "Opacity", 0, 1))

    red = int(hex_color[1:3], 16)
    green = int(hex_color[3:5], 16)
    blue = int(hex_color[5:7], 16)

    return f"rgba({red}, {green}, {blue}, {opacity_value})"


def image_file_to_data_uri(image_path: Path) -> str:
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Avatar image not found: {image_path}")

    if image_path.stat().st_size > 750_000:
        raise ValueError(
            "Avatar image is too large. Please use a smaller image, ideally under 750 KB."
        )

    mime_type, _ = mimetypes.guess_type(image_path)

    if mime_type not in ["image/png", "image/jpeg", "image/webp", "image/gif"]:
        raise ValueError("Avatar must be a PNG, JPG, WEBP, or GIF image.")

    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")

    return f"data:{mime_type};base64,{encoded}"


def build_avatar_css(style: dict[str, str]) -> str:
    user_avatar_css = ""
    assistant_avatar_css = ""

    if (
        style.get("user_avatar_enabled") == "true"
        and style.get("user_avatar_data_uri")
    ):
        user_avatar_css = f"""
.author.user {{
    background: transparent !important;
}}

.author.user img,
.author.user svg {{
    display: none !important;
}}

.author.user::before {{
    content: "";
    display: block;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background-image: url("{style["user_avatar_data_uri"]}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}
"""
    else:
        user_avatar_css = f"""
.author.user {{
    background: {style["user_bubble_color"]};
}}

.author.user img {{
    display: none;
}}

.author.user::before {{
    content: "👤";
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    font-size: 1.4rem;
}}
"""

    if (
        style.get("assistant_avatar_enabled") == "true"
        and style.get("assistant_avatar_data_uri")
    ):
        assistant_avatar_css = f"""
.author.GPT-3,
.author.GPT-4,
.author.assistant {{
    background: transparent !important;
}}

.author.GPT-3 svg,
.author.GPT-4 svg,
.author.assistant svg,
.author.GPT-3 img,
.author.GPT-4 img,
.author.assistant img {{
    display: none !important;
}}

.author.GPT-3::before,
.author.GPT-4::before,
.author.assistant::before {{
    content: "";
    display: block;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background-image: url("{style["assistant_avatar_data_uri"]}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}
"""
    else:
        assistant_avatar_css = """
.author.GPT-3,
.author.GPT-4 {
    background-color: transparent !important;
}
"""

    return user_avatar_css + assistant_avatar_css


def validate_conversation_ui_settings(style: dict[str, str]) -> dict[str, str]:
    validated = DEFAULT_CONVERSATION_UI.copy()
    validated.update(style)

    validated["background_color"] = validate_hex_color(
        validated["background_color"],
        "Background color",
    )
    validated["text_color"] = validate_hex_color(
        validated["text_color"],
        "Text color",
    )
    validated["user_bubble_color"] = validate_hex_color(
        validated["user_bubble_color"],
        "User bubble color",
    )

    validated["user_bubble_opacity"] = validate_number(
        validated["user_bubble_opacity"],
        "User bubble opacity",
        0,
        1,
    )
    validated["user_bubble_border_opacity"] = validate_number(
        validated["user_bubble_border_opacity"],
        "User bubble border opacity",
        0,
        1,
    )

    validated["font_size"] = validate_number(
        validated["font_size"],
        "Font size",
        10,
        32,
    )
    validated["line_height"] = validate_number(
        validated["line_height"],
        "Line height",
        16,
        60,
    )
    validated["conversation_max_width"] = validate_number(
        validated["conversation_max_width"],
        "Conversation max width",
        600,
        2000,
    )
    validated["user_message_max_width"] = validate_number(
        validated["user_message_max_width"],
        "User message max width",
        300,
        1600,
    )
    validated["assistant_message_max_width"] = validate_number(
        validated["assistant_message_max_width"],
        "Assistant message max width",
        300,
        1600,
    )
    validated["image_max_width"] = validate_number(
        validated["image_max_width"],
        "Image max width",
        100,
        1200,
    )

    validated["user_avatar_enabled"] = (
        "true" if str(validated.get("user_avatar_enabled", "false")).lower() == "true" else "false"
    )
    validated["assistant_avatar_enabled"] = (
        "true" if str(validated.get("assistant_avatar_enabled", "false")).lower() == "true" else "false"
    )

    validated["user_avatar_data_uri"] = str(validated.get("user_avatar_data_uri", ""))
    validated["assistant_avatar_data_uri"] = str(validated.get("assistant_avatar_data_uri", ""))

    return validated


def build_conversation_ui_patch(style: dict[str, str] | None = None) -> str:
    if style is None:
        style = get_conversation_ui_settings()

    style = validate_conversation_ui_settings(style)

    user_bubble_rgba = hex_to_rgba(
        style["user_bubble_color"],
        style["user_bubble_opacity"],
    )

    user_bubble_border_rgba = hex_to_rgba(
        style["user_bubble_color"],
        style["user_bubble_border_opacity"],
    )

    avatar_css = build_avatar_css(style)

    return f"""{PATCH_START}
<style>
/* ChatGPT Archive Builder - Generated Conversation UI */

:root {{
    --archive-bg: {style["background_color"]};
    --archive-text: {style["text_color"]};
    --archive-muted: #acacbe;
    --archive-user-bubble: {user_bubble_rgba};
    --archive-user-bubble-border: {user_bubble_border_rgba};
    --archive-border: rgba(255, 255, 255, 0.08);
}}

html,
body {{
    background: var(--archive-bg) !important;
    color: var(--archive-text) !important;
    font-family: Söhne, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif, "Helvetica Neue", Arial, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji" !important;
    font-size: {style["font_size"]}px;
    margin: 0;
    padding: 0;
}}

* {{
    box-sizing: border-box;
}}

a {{
    color: var(--archive-text);
}}

.conversation {{
    margin: 0 auto;
    padding: 1rem;
    max-width: {style["conversation_max_width"]}px !important;
}}

[data-width="narrow"] .conversation {{
    max-width: 680px !important;
}}

[data-width="wide"] .conversation {{
    max-width: 90% !important;
}}

.conversation-header {{
    margin-bottom: 1rem;
}}

.conversation-header h1 {{
    margin: 0;
}}

.conversation-header h1 a {{
    color: var(--archive-text) !important;
    font-size: 1.5rem;
    text-decoration: none;
}}

.conversation-header h1 a:hover {{
    text-decoration: underline;
}}

.conversation-header p,
.conversation-export {{
    color: var(--archive-muted);
    font-size: 0.8rem;
}}

.toggle,
.width-toggle {{
    background-color: #2f2f2f !important;
    border: 1px solid #444 !important;
    color: var(--archive-text) !important;
}}

.conversation-item {{
    display: flex;
    position: relative;
    padding: 1.5rem;
    border-left: 1px solid var(--archive-border);
    border-right: 1px solid var(--archive-border);
    border-bottom: 1px solid var(--archive-border);
}}

.conversation-item:first-of-type {{
    border-top: 1px solid var(--archive-border);
}}

.author {{
    display: flex;
    flex: 0 0 50px;
    justify-content: center;
    align-items: center;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    margin-right: 1rem;
    overflow: hidden;
}}

.author svg {{
    color: #fff;
    width: 50px;
    height: 50px;
}}

{avatar_css}

.conversation-content-wrapper {{
    display: flex;
    position: relative;
    overflow: hidden;
    flex: 1 1 auto;
    flex-direction: column;
}}

.conversation-content {{
    font-size: 1rem;
    line-height: 1.5;
}}

.conversation-content p {{
    white-space: pre-wrap;
    line-height: {style["line_height"]}px;
}}

.conversation-content img,
.conversation-content video {{
    display: block;
    max-width: {style["image_max_width"]}px;
    height: auto;
    margin-bottom: 2em;
    margin-top: 2em;
}}

.conversation-item:has(.author.user) {{
    flex-direction: row-reverse;
}}

.conversation-item:has(.author.user) .author {{
    margin-right: 0;
    margin-left: 1rem;
}}

.conversation-item:has(.author.user) .conversation-content-wrapper {{
    align-items: flex-end;
}}

.conversation-item:has(.author.user) .conversation-content {{
    text-align: left;
    background-color: var(--archive-user-bubble);
    border: 1px solid var(--archive-user-bubble-border);
    border-radius: 12px;
    padding: 8px 12px;
    max-width: min({style["user_message_max_width"]}px, 82%);
}}

.conversation-item:has(.author.user) .conversation-content img {{
    margin-left: auto;
    margin-right: 0;
}}

.conversation-item:not(:has(.author.user)) .conversation-content {{
    max-width: min({style["assistant_message_max_width"]}px, 92%);
}}
</style>
{PATCH_END}
"""


def write_generated_conversation_ui_patch(style: dict[str, str] | None = None) -> Path:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

    patch = build_conversation_ui_patch(style)

    GENERATED_PATCH_FILE.write_text(patch, encoding="utf-8")

    return GENERATED_PATCH_FILE


def save_and_generate_conversation_ui_patch(updates: dict[str, str]) -> Path:
    updated_style = update_conversation_ui_settings(updates)
    return write_generated_conversation_ui_patch(updated_style)


def reset_conversation_ui_patch() -> Path:
    style = reset_conversation_ui_settings()
    return write_generated_conversation_ui_patch(style)