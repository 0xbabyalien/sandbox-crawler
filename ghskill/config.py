from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "sources.json"


def load_config(path=None):
    p = Path(path) if path else DEFAULT_CONFIG
    return json.loads(p.read_text(encoding="utf-8"))
