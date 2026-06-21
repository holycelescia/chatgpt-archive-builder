# Template loading and rendering.

from html import escape
from pathlib import Path


LINKS_START = "<!-- AUTO-GENERATED-LINKS-START -->"
LINKS_END = "<!-- AUTO-GENERATED-LINKS-END -->"


def load_template(template_path: Path) -> str:
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    return template_path.read_text(encoding="utf-8")


def save_html(output_path: Path, html: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def build_link_list(items: list[dict[str, str]]) -> str:
    lines = ["<ul>"]

    for item in items:
        title = escape(item["title"])
        href = escape(item["href"], quote=True)
        lines.append(f'  <li><a href="{href}">{title}</a></li>')

    lines.append("</ul>")
    return "\n".join(lines)


def replace_auto_generated_links(template: str, items: list[dict[str, str]]) -> str:
    start_index = template.find(LINKS_START)
    end_index = template.find(LINKS_END)

    if start_index == -1 or end_index == -1:
        raise ValueError("Template is missing auto-generated links markers.")

    if end_index < start_index:
        raise ValueError("Auto-generated links markers are in the wrong order.")

    before = template[: start_index + len(LINKS_START)]
    after = template[end_index:]

    generated_links = build_link_list(items)

    return f"{before}\n{generated_links}\n{after}"


def render_home(template_path: Path, output_path: Path, folders: list[str]) -> None:
    template = load_template(template_path)

    items = [
        {
            "title": folder,
            "href": f"{folder}/index.html",
        }
        for folder in folders
    ]

    html = replace_auto_generated_links(template, items)
    save_html(output_path, html)


def render_menu(
    template_path: Path,
    output_path: Path,
    title: str,
    folders: list[str | dict[str, str]],
    home_href: str = "../index.html",
    back_href: str = "../index.html",
) -> None:
    template = load_template(template_path)

    items = []

    for folder in folders:
        if isinstance(folder, dict):
            items.append(
                {
                    "title": folder["title"],
                    "href": folder["href"],
                }
            )
        else:
            items.append(
                {
                    "title": folder,
                    "href": f"{folder}/index.html",
                }
            )

    html = template.replace("CATEGORY", escape(title))
    html = html.replace("{{HOME_HREF}}", escape(home_href, quote=True))
    html = html.replace("{{BACK_HREF}}", escape(back_href, quote=True))
    html = replace_auto_generated_links(html, items)

    save_html(output_path, html)


def render_month(
    template_path: Path,
    output_path: Path,
    month_title: str,
    conversations: list[str],
    home_href: str = "../../../index.html",
    back_href: str = "../index.html",
) -> None:
    template = load_template(template_path)

    items = [
        {
            "title": conversation,
            "href": f"{conversation}.html",
        }
        for conversation in conversations
    ]

    html = template.replace("MONTH", escape(month_title))
    html = html.replace("{{HOME_HREF}}", escape(home_href, quote=True))
    html = html.replace("{{BACK_HREF}}", escape(back_href, quote=True))
    html = replace_auto_generated_links(html, items)

    save_html(output_path, html)