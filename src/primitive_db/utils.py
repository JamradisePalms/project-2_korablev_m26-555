# Вспомогательные тулы
import json
from pathlib import Path


def load_metadata(filepath: Path | str) -> dict:
    if isinstance(filepath, str):
        filepath = Path(filepath)

    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_metadata(filepath: Path | str, data: dict) -> None:
    if isinstance(filepath, str):
        filepath = Path(filepath)

    with open(filepath, "w") as f:
        json.dump(data, f)
