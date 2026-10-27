import json
from pathlib import Path

from .constants import DATA_DIR


def validate_table_name(table_name: str) -> None:
    """Не допускает пустое имя и использование имени таблицы как пути."""
    if table_name in ("", ".", "..") or any(
        char in table_name for char in ("/", "\\", "\0")
    ):
        raise ValueError("Имя таблицы не должно быть пустым или содержать путь")


def load_metadata(filepath: Path | str) -> dict:
    """Загружает метаданные; если файла нет, возвращает пустой словарь."""
    if isinstance(filepath, str):
        filepath = Path(filepath)

    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_metadata(filepath: Path | str, data: dict) -> None:
    """Сохраняет метаданные в JSON-файл."""
    if isinstance(filepath, str):
        filepath = Path(filepath)

    with open(filepath, "w") as f:
        json.dump(data, f)

def load_table_data(table_name: str) -> list:
    """Загружает записи таблицы из JSON-файла."""
    validate_table_name(table_name)
    table_data = DATA_DIR / f"{table_name}.json"

    with open(table_data, "r") as f:
        return json.load(f)

def save_table_data(table_name: str, data: list) -> None:
    """Сохраняет записи таблицы, создавая папку данных при необходимости."""
    validate_table_name(table_name)
    table_data = DATA_DIR / f"{table_name}.json"

    table_data.parent.mkdir(parents=True, exist_ok=True)

    with open(table_data, "w") as f:
        json.dump(data, f)
