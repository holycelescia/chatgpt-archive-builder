from pathlib import Path
import re
from conversation_style_manager import GENERATED_PATCH_FILE
from config import CONVERSATION_UI_PATCH


PATCH_START = "<!-- ARCHIVER-CONVERSATION-UI-START -->"
PATCH_END = "<!-- ARCHIVER-CONVERSATION-UI-END -->"

PATCH_PATTERN = re.compile(
    re.escape(PATCH_START) + r".*?" + re.escape(PATCH_END),
    re.IGNORECASE | re.DOTALL,
)

HEAD_END_PATTERN = re.compile(r"</head>", re.IGNORECASE)


def read_text_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return path.read_text(encoding="utf-8")


def write_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def load_ui_patch() -> str:
    patch_path = GENERATED_PATCH_FILE if GENERATED_PATCH_FILE.exists() else CONVERSATION_UI_PATCH

    patch = read_text_file(patch_path)

    if PATCH_START not in patch or PATCH_END not in patch:
        raise ValueError(
            "Conversation UI patch is missing ARCHIVER-CONVERSATION-UI markers."
        )

    return patch.strip()


def is_index_file(path: Path) -> bool:
    return path.name.lower() == "index.html"


def get_html_conversation_files(folder_path: Path) -> list[Path]:
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    if not folder_path.is_dir():
        raise NotADirectoryError(f"Not a folder: {folder_path}")

    return sorted(
        [
            path
            for path in folder_path.glob("*.html")
            if not is_index_file(path)
        ],
        key=lambda path: path.name.casefold(),
    )


def apply_ui_patch_to_html(html: str, patch: str) -> str:
    if PATCH_START in html and PATCH_END in html:
        return PATCH_PATTERN.sub(patch, html)

    if not HEAD_END_PATTERN.search(html):
        raise ValueError("HTML file is missing </head>. Cannot inject UI patch.")

    return HEAD_END_PATTERN.sub(f"\n{patch}\n</head>", html, count=1)


def apply_ui_patch_to_file(file_path: Path) -> bool:
    patch = load_ui_patch()
    original_html = read_text_file(file_path)

    updated_html = apply_ui_patch_to_html(original_html, patch)

    if updated_html == original_html:
        return False

    write_text_file(file_path, updated_html)
    return True


def apply_ui_patch_to_folder(folder_path: Path) -> dict[str, object]:
    conversation_files = get_html_conversation_files(folder_path)

    changed_files = []
    unchanged_files = []

    for file_path in conversation_files:
        was_changed = apply_ui_patch_to_file(file_path)

        if was_changed:
            changed_files.append(file_path)
        else:
            unchanged_files.append(file_path)

    return {
        "folder_path": folder_path,
        "total_files": len(conversation_files),
        "changed_count": len(changed_files),
        "unchanged_count": len(unchanged_files),
        "changed_files": changed_files,
        "unchanged_files": unchanged_files,
    }