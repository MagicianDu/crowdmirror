from pathlib import Path
import sys


def bootstrap_src_path() -> None:
    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"
    src = str(src_path)
    if src_path.exists() and src not in sys.path:
        sys.path.insert(0, src)
