# Archive building workflow.

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

TEMPLATE_DIR = REPO_ROOT / "templates" / "default"

OUTPUT_DIR = REPO_ROOT / "output"
TEST_ARCHIVE_DIR = OUTPUT_DIR / "test_archive"

HOME_TEMPLATE = TEMPLATE_DIR / "home_index.html"
MENU_TEMPLATE = TEMPLATE_DIR / "menu_index.html"
MONTH_TEMPLATE = TEMPLATE_DIR / "month_index.html"
CONVERSATION_UI_PATCH = TEMPLATE_DIR / "conversation_ui_patch.html"