"""プロジェクト共通のパス定義と設定。"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CONTENTS_DIR = PROJECT_ROOT / "contents"

MEGA_REMOTE_DEST = "/book"
