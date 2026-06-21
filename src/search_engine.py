# Search logic.

from pathlib import Path
from html import unescape
import re


CONVERSATION_CONTENT_PATTERN = re.compile(
    r'<div\s+class="[^"]*\bconversation-content\b[^"]*"\s*>(.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)

MESSAGE_ROLE_PATTERN = re.compile(
    r'<div[^>]*data-message-author-role="(?:user|assistant)"[^>]*>(.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)

TITLE_PATTERN = re.compile(
    r"<title>(.*?)</title>",
    re.IGNORECASE | re.DOTALL,
)


def parse_keywords(raw_keywords: str) -> list[str]:
    keywords = [
        keyword.strip()
        for keyword in re.split(r"[;,]", raw_keywords)
        if keyword.strip()
    ]

    if not keywords:
        raise ValueError("No keywords entered.")

    return keywords


def is_index_file(path: Path) -> bool:
    return path.name.lower() == "index.html"


def is_inside_mhtml_folder(path: Path) -> bool:
    return any(part.lower() == "mhtml" for part in path.parts)


def get_html_files(root_path: Path) -> list[Path]:
    if not root_path.exists():
        raise FileNotFoundError(f"Folder not found: {root_path}")

    if not root_path.is_dir():
        raise NotADirectoryError(f"Not a folder: {root_path}")

    files = []

    for path in root_path.rglob("*.html"):
        if is_index_file(path):
            continue

        if is_inside_mhtml_folder(path):
            continue

        files.append(path)

    return sorted(files, key=lambda file_path: str(file_path).casefold())


def clean_html_to_text(html: str) -> str:
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</p>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)

    text = unescape(html)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_conversation_html(html: str) -> str:
    conversation_blocks = CONVERSATION_CONTENT_PATTERN.findall(html)

    if conversation_blocks:
        return " ".join(conversation_blocks)

    role_blocks = MESSAGE_ROLE_PATTERN.findall(html)

    if role_blocks:
        return " ".join(role_blocks)

    return ""


def extract_searchable_text(html: str) -> str:
    conversation_html = extract_conversation_html(html)

    if not conversation_html:
        return ""

    return clean_html_to_text(conversation_html)


def extract_title(html: str, fallback: str) -> str:
    match = TITLE_PATTERN.search(html)

    if not match:
        return fallback

    title = clean_html_to_text(match.group(1))

    return title if title else fallback


def file_contains_all_keywords(text: str, keywords: list[str]) -> bool:
    normalized_text = text.casefold()

    for keyword in keywords:
        if keyword.casefold() not in normalized_text:
            return False

    return True


def search_archive(root_path: Path, raw_keywords: str) -> dict[str, object]:
    keywords = parse_keywords(raw_keywords)
    html_files = get_html_files(root_path)

    results = []
    skipped_files = 0

    for file_path in html_files:
        try:
            html = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            html = file_path.read_text(encoding="utf-8", errors="ignore")

        searchable_text = extract_searchable_text(html)

        if not searchable_text:
            skipped_files += 1
            continue

        if file_contains_all_keywords(searchable_text, keywords):
            try:
                relative_path = file_path.relative_to(root_path)
            except ValueError:
                relative_path = file_path

            results.append(
                {
                    "title": extract_title(html, file_path.stem),
                    "file_path": file_path,
                    "relative_path": relative_path,
                }
            )

    return {
        "root_path": root_path,
        "keywords": keywords,
        "files_scanned": len(html_files),
        "files_skipped": skipped_files,
        "results": results,
    }