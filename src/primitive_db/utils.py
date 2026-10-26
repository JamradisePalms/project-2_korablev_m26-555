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

def load_table_data(table_name: str) -> list:
    table_data = Path(f"data/{table_name}.json")

    if not table_data.exists():
        raise ValueError(f"Ошибка: Таблица {table_name} не существует")

    with open(table_data, "r") as f:
        return json.load(f)

def save_table_data(table_name: str, data: list) -> None:
    table_data = Path(f"data/{table_name}.json")

    table_data.parent.mkdir(parents=True, exist_ok=True)

    with open(table_data, "w") as f:
        json.dump(data, f)
