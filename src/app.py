from pathlib import Path

from folder_manager import build_archive, build_test_archive, normalize_folder_names, create_archive_folder
from conversation_converter import apply_ui_patch_to_folder
from updater import update_conversation_index
from search_engine import search_archive
from settings_manager import get_archive_root, set_archive_root, clear_archive_root


def print_header() -> None:
    print()
    print("ChatGPT Archive Builder")
    print("=======================")
    print()


def print_menu() -> None:
    print("What would you like to do?")
    print()
    print("1. Build new archive")
    print("2. Build test archive")
    print("3. Add folder to archive")
    print("4. Update conversation folder")
    print("5. Search archive")
    print("6. Show saved archive root")
    print("7. Clear saved archive root")
    print("8. Exit")
    print()


def build_new_archive_from_menu() -> None:
    folder_input = input("Paste the folder path where the archive should be created: ").strip().strip('"')
    archive_root = Path(folder_input)

    print()
    print("Optional: add top-level folders such as Projects, Stories, NSFW.")
    print("Separate multiple folders with commas.")
    raw_extra_folders = input("Extra folders, or leave empty: ").strip()

    extra_folders = normalize_folder_names(raw_extra_folders)

    archive_path = build_archive(
        archive_root=archive_root,
        extra_folders=extra_folders,
    )

    set_archive_root(archive_path)

    print()
    print("Archive created.")
    print(f"Archive folder: {archive_path}")
    print(f"Open this file in your browser: {archive_path / 'index.html'}")
    print("Archive root saved for future actions.")

    if extra_folders:
        print()
        print("Extra folders created:")
        for folder in extra_folders:
            print(f"- {folder}")

    print()


def build_test_archive_from_menu() -> None:
    archive_path = build_test_archive()

    print()
    print("Test archive created.")
    print(f"Archive folder: {archive_path}")
    print(f"Open this file in your browser: {archive_path / 'index.html'}")
    print()


def update_conversation_folder() -> None:
    folder_input = input("Paste the conversation folder path to update: ").strip().strip('"')
    folder_path = Path(folder_input)

    print()
    print("Applying conversation UI patch...")
    patch_result = apply_ui_patch_to_folder(folder_path)

    print(f"HTML conversation files found: {patch_result['total_files']}")
    print(f"Files updated with UI patch: {patch_result['changed_count']}")
    print(f"Files already up to date: {patch_result['unchanged_count']}")

    print()
    print("Updating folder index...")
    index_result = update_conversation_index(folder_path)

    print()
    print("Archive folder update complete.")
    print(f"Index file: {index_result['index_path']}")
    print(f"New conversations added to index: {index_result['added_count']}")
    print(f"Total conversations listed: {index_result['total_links']}")

    if index_result["added_links"]:
        print()
        print("Added to index:")
        for link in index_result["added_links"]:
            print(f"- {link['title']} -> {link['href']}")

    print()


def search_archive_from_menu() -> None:
    
    saved_archive_root = get_archive_root()

    root_path = ask_path_with_saved_default(
        "Archive or folder path to search: ",
        saved_archive_root,
    )

    raw_keywords = input("Enter keyword(s), separated by comma or semicolon: ").strip()

    print()
    print("Searching archive...")

    try:
        search_result = search_archive(root_path, raw_keywords)
    except ValueError as error:
        print(f"Search error: {error}")
        return

    results = search_result["results"]

    print()
    print("Search complete.")
    print(f"Folder searched: {search_result['root_path']}")
    print(f"Keywords: {' | '.join(search_result['keywords'])}")
    print(f"HTML conversation files scanned: {search_result['files_scanned']}")
    print(f"Files skipped because no conversation content was detected: {search_result['files_skipped']}")
    print(f"Results found: {len(results)}")

    if not results:
        print()
        print("No conversation found.")
        return

    print()
    print("Results:")

    for result in results:
        print()
        print(f">> {result['title']}")
        print(f"   {result['relative_path']}")
        print(f"   {result['file_path']}")

def ask_path_with_saved_default(prompt: str, saved_path: Path | None) -> Path:
    if saved_path:
        print(f"Saved archive root: {saved_path}")
        print("Press Enter to use it, or paste another path.")
        raw_path = input(prompt).strip().strip('"')

        if not raw_path:
            return saved_path

        return Path(raw_path)

    raw_path = input(prompt).strip().strip('"')
    return Path(raw_path)


def show_saved_archive_root_from_menu() -> None:
    archive_root = get_archive_root()

    print()

    if archive_root:
        print(f"Saved archive root: {archive_root}")
    else:
        print("No archive root saved yet.")

    print()


def clear_saved_archive_root_from_menu() -> None:
    clear_archive_root()

    print()
    print("Saved archive root cleared.")
    print()

def add_folder_to_archive_from_menu() -> None:
    saved_archive_root = get_archive_root()

    archive_root = ask_path_with_saved_default(
        "Archive root path: ",
        saved_archive_root,
    )

    parent_folder_input = input("Paste the parent folder path where the new folder should be created: ").strip().strip('"')
    folder_name = input("New folder name: ").strip()

    print()
    print("What type of folder is this?")
    print("1. Menu folder")
    print("2. Conversation folder")
    print()

    type_choice = input("Enter your choice: ").strip()

    if type_choice == "1":
        index_type = "menu"
    elif type_choice == "2":
        index_type = "conversation"
    else:
        print()
        print("Invalid folder type. Please enter 1 or 2.")
        return

    try:
        result = create_archive_folder(
            archive_root=archive_root,
            parent_folder=Path(parent_folder_input),
            folder_name=folder_name,
            index_type=index_type,
        )
    except (FileNotFoundError, ValueError) as error:
        print()
        print(f"Folder creation error: {error}")
        return

    print()
    print("Folder created.")
    print(f"Folder: {result['new_folder']}")
    print(f"Index file: {result['new_index']}")
    print(f"Index type: {result['index_type']}")
    print(f"Parent index updated: {result['parent_index']}")

    parent_update = result["parent_update"]

    if parent_update["was_added"]:
        print("New folder link added to parent index.")
    else:
        print("Folder link was already present in parent index.")

    print(f"Total links in parent index: {parent_update['total_links']}")
    print()


def main() -> None:
    while True:
        print_header()
        print_menu()

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            build_new_archive_from_menu()
        elif choice == "2":
            build_test_archive_from_menu()
        elif choice == "3":
            add_folder_to_archive_from_menu()
        elif choice == "4":
            update_conversation_folder()
        elif choice == "5":
            search_archive_from_menu()
        elif choice == "6":
            show_saved_archive_root_from_menu()
        elif choice == "7":
            clear_saved_archive_root_from_menu()
        elif choice == "8":
            print()
            print("Goodbye.")
            break
        else:
            print()
            print("Invalid choice. Please enter a number between 1 and 8.")

        print()
        input("Press Enter to return to the menu...")
    
    


if __name__ == "__main__":
    main()