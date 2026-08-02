import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

def load_last_output_folder(default: str) -> str:
    if not CONFIG_PATH.exists():
        return default
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        folder = data.get("last_output_folder")
        if folder and Path(folder).is_dir():
            return folder
    except (json.JSONDecodeError, OSError):
        pass
    return default

def save_last_output_folder(folder: str) -> None:
    try:
        CONFIG_PATH.write_text(
            json.dumps({"last_output_folder": folder}), encoding="utf-8"
        )
    except OSError:
        pass
    