# Folder creation and index management.
import os
from datetime import datetime
from pathlib import Path
import calendar
import re

from updater import add_folder_link_to_index
from config import HOME_TEMPLATE, MENU_TEMPLATE, MONTH_TEMPLATE, TEST_ARCHIVE_DIR
from template_renderer import render_home, render_menu, render_month


def get_current_year_and_month() -> tuple[str, str]:
    now = datetime.now()
    year = str(now.year)
    month = now.strftime("%B %Y")
    return year, month


def normalize_folder_names(raw_folders: str) -> list[str]:
    if not raw_folders.strip():
        return []

    folders = []

    for folder in raw_folders.replace(";", ",").split(","):
        cleaned = folder.strip()

        if cleaned:
            folders.append(cleaned)

    return folders

def parse_years(raw_years: str) -> list[int]:
    current_year = datetime.now().year

    if not raw_years.strip():
        return [current_year]

    parts = re.split(r"[,;\s]+", raw_years.strip())
    years = []

    for part in parts:
        if not part:
            continue

        if not part.isdigit():
            raise ValueError(f"Invalid year: {part}")

        year = int(part)

        if year < 2000 or year > 2100:
            raise ValueError(f"Year must be between 2000 and 2100: {year}")

        years.append(year)

    if not years:
        return [current_year]

    return sorted(set(years))


def build_archive(
    archive_root: Path,
    extra_folders: list[str] | None = None,
    years_to_create: list[int] | None = None,
    create_all_months: bool = False,
) -> Path:
    now = datetime.now()
    current_year = now.year
    current_month = now.strftime("%B %Y")

    if years_to_create is None:
        years_to_create = [current_year]

    years_to_create = sorted(set(years_to_create))

    extra_folders = extra_folders or []

    archive_root.mkdir(parents=True, exist_ok=True)

    conversations_folder = archive_root / "Conversations"
    conversations_folder.mkdir(parents=True, exist_ok=True)

    home_folders = ["Conversations"] + extra_folders

    render_home(
        template_path=HOME_TEMPLATE,
        output_path=archive_root / "index.html",
        folders=home_folders,
    )

    for folder_name in extra_folders:
        folder_path = archive_root / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)

        render_menu(
            template_path=MENU_TEMPLATE,
            output_path=folder_path / "index.html",
            title=folder_name,
            folders=[],
            home_href="../index.html",
            back_href="../index.html",
        )

    conversation_year_links = [
        {
            "title": str(year),
            "href": f"{year}/index.html",
        }
        for year in years_to_create
    ]

    render_menu(
        template_path=MENU_TEMPLATE,
        output_path=conversations_folder / "index.html",
        title="Conversations",
        folders=conversation_year_links,
        home_href="../index.html",
        back_href="../index.html",
    )

    for year in years_to_create:
        year_folder = conversations_folder / str(year)
        year_folder.mkdir(parents=True, exist_ok=True)

        if create_all_months:
            month_names = [
                f"{calendar.month_name[month_number]} {year}"
                for month_number in range(1, 13)
            ]
        else:
            if year == current_year:
                month_names = [current_month]
            else:
                month_names = []

        month_links = [
            {
                "title": month_name.replace(f" {year}", ""),
                "href": f"{month_name}/index.html",
            }
            for month_name in month_names
        ]

        render_menu(
            template_path=MENU_TEMPLATE,
            output_path=year_folder / "index.html",
            title=str(year),
            folders=month_links,
            home_href="../../index.html",
            back_href="../index.html",
        )

        for month_name in month_names:
            month_folder = year_folder / month_name
            month_folder.mkdir(parents=True, exist_ok=True)

            render_month(
                template_path=MONTH_TEMPLATE,
                output_path=month_folder / "index.html",
                month_title=month_name,
                conversations=[],
                home_href="../../../index.html",
                back_href="../index.html",
            )

    return archive_root


def build_test_archive() -> Path:
    return build_archive(
        archive_root=TEST_ARCHIVE_DIR,
        extra_folders=[
            "Projects",
            "Stories",
        ],
    )

def make_relative_href(from_folder: Path, target_file: Path) -> str:
    relative_path = os.path.relpath(target_file, start=from_folder)
    return relative_path.replace("\\", "/")


def validate_folder_name(folder_name: str) -> str:
    cleaned = folder_name.strip()

    if not cleaned:
        raise ValueError("Folder name cannot be empty.")

    forbidden_characters = '<>:"/\\|?*'

    for character in forbidden_characters:
        if character in cleaned:
            raise ValueError(f"Folder name contains forbidden character: {character}")

    return cleaned


def create_archive_folder(
    archive_root: Path,
    parent_folder: Path,
    folder_name: str,
    index_type: str,
) -> dict[str, object]:
    folder_name = validate_folder_name(folder_name)

    archive_root = archive_root.resolve()
    parent_folder = parent_folder.resolve()

    parent_index = parent_folder / "index.html"

    if not archive_root.exists():
        raise FileNotFoundError(f"Archive root not found: {archive_root}")

    if not parent_folder.exists():
        raise FileNotFoundError(f"Parent folder not found: {parent_folder}")

    if not parent_index.exists():
        raise FileNotFoundError(f"Parent index.html not found: {parent_index}")

    new_folder = parent_folder / folder_name
    new_folder.mkdir(parents=True, exist_ok=True)

    new_index = new_folder / "index.html"

    home_href = make_relative_href(new_folder, archive_root / "index.html")
    back_href = make_relative_href(new_folder, parent_index)

    if index_type == "menu":
        render_menu(
            template_path=MENU_TEMPLATE,
            output_path=new_index,
            title=folder_name,
            folders=[],
            home_href=home_href,
            back_href=back_href,
        )
    elif index_type == "conversation":
        render_month(
            template_path=MONTH_TEMPLATE,
            output_path=new_index,
            month_title=folder_name,
            conversations=[],
            home_href=home_href,
            back_href=back_href,
        )
    else:
        raise ValueError("index_type must be 'menu' or 'conversation'.")

    parent_update = add_folder_link_to_index(
        index_path=parent_index,
        folder_title=folder_name,
        folder_href=f"{folder_name}/index.html",
    )

    return {
        "new_folder": new_folder,
        "new_index": new_index,
        "index_type": index_type,
        "parent_index": parent_index,
        "parent_update": parent_update,
    }