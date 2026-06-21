# Archive update logic.

from pathlib import Path
from html import escape
import re
from template_renderer import replace_auto_generated_links

from template_renderer import LINKS_START, LINKS_END


LINK_PATTERN = re.compile(
    r'<li>\s*<a\s+href="(?P<href>[^"]+)">(?P<title>.*?)</a>\s*</li>',
    re.IGNORECASE | re.DOTALL,
)


def read_html_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return path.read_text(encoding="utf-8")


def write_html_file(path: Path, html: str) -> None:
    path.write_text(html, encoding="utf-8")


def get_auto_generated_section(html: str) -> tuple[int, int]:
    start_index = html.find(LINKS_START)
    end_index = html.find(LINKS_END)

    if start_index == -1 or end_index == -1:
        raise ValueError("Index file is missing auto-generated links markers.")

    if end_index < start_index:
        raise ValueError("Auto-generated links markers are in the wrong order.")

    return start_index, end_index


def extract_existing_links(html: str) -> list[dict[str, str]]:
    start_index, end_index = get_auto_generated_section(html)

    section = html[start_index + len(LINKS_START):end_index]

    links = []

    for match in LINK_PATTERN.finditer(section):
        href = match.group("href").strip()
        title = match.group("title").strip()

        if href == "TITRE.html" or title == "TITRE":
            continue

        links.append(
            {
                "href": href,
                "title": title,
            }
        )

    return links


def get_conversation_files(folder_path: Path) -> list[Path]:
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    if not folder_path.is_dir():
        raise NotADirectoryError(f"Not a folder: {folder_path}")

    html_files = []

    for file_path in folder_path.glob("*.html"):
        if file_path.name.lower() == "index.html":
            continue

        html_files.append(file_path)

    return sorted(html_files, key=lambda path: path.stem.casefold())


def build_link_list(links: list[dict[str, str]]) -> str:
    lines = ["<ul>"]

    for link in links:
        href = escape(link["href"], quote=True)
        title = escape(link["title"])
        lines.append(f'  <li><a href="{href}">{title}</a></li>')

    lines.append("</ul>")
    return "\n".join(lines)


def replace_links_section(html: str, links: list[dict[str, str]]) -> str:
    start_index, end_index = get_auto_generated_section(html)

    before = html[: start_index + len(LINKS_START)]
    after = html[end_index:]

    generated_links = build_link_list(links)

    return f"{before}\n{generated_links}\n{after}"


def update_conversation_index(folder_path: Path) -> dict[str, object]:
    index_path = folder_path / "index.html"

    html = read_html_file(index_path)

    existing_links = extract_existing_links(html)
    existing_links_by_href = {
        link["href"]: link
        for link in existing_links
    }

    conversation_files = get_conversation_files(folder_path)

    updated_links = []
    added_links = []

    for file_path in conversation_files:
        href = file_path.name
        title = file_path.stem

        if href in existing_links_by_href:
            updated_links.append(existing_links_by_href[href])
            continue

        new_link = {
            "href": href,
            "title": title,
        }

        updated_links.append(new_link)
        added_links.append(new_link)

    updated_links = sorted(updated_links, key=lambda link: link["title"].casefold())

    updated_html = replace_links_section(html, updated_links)
    write_html_file(index_path, updated_html)

    return {
        "index_path": index_path,
        "added_count": len(added_links),
        "total_links": len(updated_links),
        "added_links": added_links,
    }

    updated_html = replace_links_section(html, existing_links)
    write_html_file(index_path, updated_html)

    return {
        "index_path": index_path,
        "added_count": len(added_links),
        "total_links": len(existing_links),
        "added_links": added_links,
    }

def get_menu_subfolders(folder_path: Path) -> list[Path]:
    folder_path = Path(folder_path)

    subfolders = []

    for child in folder_path.iterdir():
        if not child.is_dir():
            continue

        if not (child / "index.html").exists():
            continue

        subfolders.append(child)

    return sorted(subfolders, key=lambda path: path.name.lower())


def get_menu_display_title(parent_folder: Path, child_folder: Path) -> str:
    title = child_folder.name
    parent_name = parent_folder.name

    if parent_name.isdigit() and title.endswith(f" {parent_name}"):
        return title.removesuffix(f" {parent_name}")

    return title


def update_menu_index(folder_path: Path) -> dict:
    folder_path = Path(folder_path)
    index_path = folder_path / "index.html"

    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    if not index_path.exists():
        raise FileNotFoundError(f"Index file not found: {index_path}")

    subfolders = get_menu_subfolders(folder_path)

    folder_links = [
        {
            "title": get_menu_display_title(folder_path, subfolder),
            "href": f"{subfolder.name}/index.html",
        }
        for subfolder in subfolders
    ]

    html = index_path.read_text(encoding="utf-8", errors="ignore")
    updated_html = replace_auto_generated_links(html, folder_links)

    index_path.write_text(updated_html, encoding="utf-8")

    return {
        "folder_path": folder_path,
        "index_path": index_path,
        "total_folders": len(folder_links),
        "folder_links": folder_links,
    }

def add_folder_link_to_index(index_path: Path, folder_title: str, folder_href: str) -> dict[str, object]:
    html = read_html_file(index_path)

    existing_links = extract_existing_links(html)
    existing_hrefs = {link["href"] for link in existing_links}

    added = False

    if folder_href not in existing_hrefs:
        existing_links.append(
            {
                "title": folder_title,
                "href": folder_href,
            }
        )
        added = True

    existing_links = sorted(existing_links, key=lambda link: link["title"].casefold())

    updated_html = replace_links_section(html, existing_links)
    write_html_file(index_path, updated_html)

    return {
        "index_path": index_path,
        "folder_title": folder_title,
        "folder_href": folder_href,
        "was_added": added,
        "total_links": len(existing_links),
    }