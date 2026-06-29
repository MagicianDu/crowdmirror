"""Dataset download utilities."""

import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "raw"


def ensure_swissmetro() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "swissmetro.dat"
    if not path.exists():
        url = "https://raw.githubusercontent.com/michelbierlaire/biogeme/master/tests/swissmetro/swissmetro.dat"
        urllib.request.urlretrieve(url, path)
    return path
