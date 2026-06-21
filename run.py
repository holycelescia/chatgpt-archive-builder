from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from ui import main


if __name__ == "__main__":
    main()