from pathlib import Path
import py_compile
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
TEMPLATE_DIR = REPO_ROOT / "templates" / "default"

REQUIRED_FILES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "requirements.txt",
    REPO_ROOT / "version.txt",
    REPO_ROOT / ".gitignore",
    SRC_DIR / "ui.py",
    SRC_DIR / "folder_manager.py",
    SRC_DIR / "conversation_converter.py",
    SRC_DIR / "conversation_style_manager.py",
    SRC_DIR / "settings_manager.py",
    SRC_DIR / "search_engine.py",
    SRC_DIR / "updater.py",
    TEMPLATE_DIR / "home_index.html",
    TEMPLATE_DIR / "menu_index.html",
    TEMPLATE_DIR / "month_index.html",
    TEMPLATE_DIR / "conversation_ui_patch.html",
]

PRIVATE_FILES_THAT_SHOULD_NOT_BE_TRACKED = [
    REPO_ROOT / "settings" / "settings.json",
    REPO_ROOT / "settings" / "generated_conversation_ui_patch.html",
]

REQUIRED_GITIGNORE_LINES = [
    "settings/*.json",
    "settings/generated_conversation_ui_patch.html",
    "output/",
    "archives/",
    ".venv/",
]


def check_required_files() -> list[str]:
    errors = []

    for file_path in REQUIRED_FILES:
        if not file_path.exists():
            errors.append(f"Missing required file: {file_path.relative_to(REPO_ROOT)}")

    return errors


def check_python_compile() -> list[str]:
    errors = []

    for file_path in SRC_DIR.rglob("*.py"):
        try:
            py_compile.compile(str(file_path), doraise=True)
        except py_compile.PyCompileError as error:
            errors.append(f"Python compile failed: {file_path.relative_to(REPO_ROOT)}\n{error}")

    return errors


def check_version_match() -> list[str]:
    errors = []

    version_file = REPO_ROOT / "version.txt"
    ui_file = SRC_DIR / "ui.py"

    if not version_file.exists() or not ui_file.exists():
        return errors

    version = version_file.read_text(encoding="utf-8").strip()
    ui_text = ui_file.read_text(encoding="utf-8")

    expected_line = f'APP_VERSION = "v{version}"'

    if expected_line not in ui_text:
        errors.append(
            "Version mismatch: version.txt says "
            f"{version}, but ui.py does not contain {expected_line}"
        )

    return errors


def check_gitignore() -> list[str]:
    errors = []

    gitignore_path = REPO_ROOT / ".gitignore"

    if not gitignore_path.exists():
        return ["Missing .gitignore"]

    gitignore_text = gitignore_path.read_text(encoding="utf-8")

    for required_line in REQUIRED_GITIGNORE_LINES:
        if required_line not in gitignore_text:
            errors.append(f".gitignore is missing: {required_line}")

    return errors


def check_private_files_warning() -> list[str]:
    warnings = []

    for file_path in PRIVATE_FILES_THAT_SHOULD_NOT_BE_TRACKED:
        if file_path.exists():
            warnings.append(
                f"Private local file exists, make sure GitHub Desktop is NOT tracking it: "
                f"{file_path.relative_to(REPO_ROOT)}"
            )

    return warnings


def main() -> int:
    print("ChatGPT Archive Builder preflight check")
    print("=" * 42)

    checks = [
        ("Required files", check_required_files),
        ("Python compile", check_python_compile),
        ("Version match", check_version_match),
        (".gitignore", check_gitignore),
    ]

    all_errors = []

    for label, check_function in checks:
        print(f"\nChecking {label}...")
        errors = check_function()

        if errors:
            print("FAILED")
            all_errors.extend(errors)
        else:
            print("OK")

    warnings = check_private_files_warning()

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")

    if all_errors:
        print("\nErrors:")
        for error in all_errors:
            print(f"- {error}")

        print("\nPreflight failed. The goblin found problems.")
        return 1

    print("\nPreflight passed. The goblin found nothing catastrophic.")
    return 0


if __name__ == "__main__":
    sys.exit(main())