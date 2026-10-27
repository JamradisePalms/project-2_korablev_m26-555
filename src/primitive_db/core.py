from .constants import TYPES_WHITELIST
from .decorators import confirm_action, handle_db_errors, log_time
from .errors import TableNotFoundError
from .utils import load_table_data, save_table_data, validate_table_name


@handle_db_errors
def create_table(metadata: dict, table_name: str, columns: list) -> dict | None:
    """Проверяет столбцы и добавляет схему новой таблицы в метаданные."""
    validate_table_name(table_name)
    if table_name in metadata:
        raise ValueError(f"Таблица {table_name} уже существует")

    columns_metadata = []
    column_names = set()
    for column in columns:
        column_name, column_type = column.split(":")
        if column_name in column_names:
            raise ValueError(f"Столбец {column_name} указан несколько раз")
        if column_type not in TYPES_WHITELIST:
            raise ValueError(f"Invalid column type: {column_type}")
        if column_name == "ID" and column_type != "int":
            raise ValueError("Столбец ID должен иметь тип int")
        column_names.add(column_name)
        columns_metadata.append({"type": column_type, "name": column_name})

    id_index = next(
        (index for index, column in enumerate(columns_metadata)
         if column["name"] == "ID"),
        None,
    )
    if id_index is None:
        columns_metadata.insert(0, {"type": "int", "name": "ID"})
    elif id_index != 0:
        columns_metadata.insert(0, columns_metadata.pop(id_index))
        print("WARNING! Столбец ID:int перенесён в начало таблицы")

    updated_columns = [
        f"{column['name']}:{column['type']}" for column in columns_metadata
    ]
    metadata[table_name] = {"columns": columns_metadata}

    print(f"Таблица {table_name} успешно создана со столбцами: {updated_columns}")
    return metadata

@confirm_action("удалить таблицу")
@handle_db_errors
def drop_table(metadata: dict, table_name: str) -> dict | None:
    """Удаляет схему таблицы из метаданных после подтверждения."""
    copy_metadata = metadata.copy()

    if table_name not in copy_metadata:
        raise TableNotFoundError(f"Таблица {table_name} не существует")

    del copy_metadata[table_name]

    print(f"Таблица {table_name} успешно удалена")

    return copy_metadata

@log_time
@handle_db_errors
def insert(metadata: dict, table_name: str, values: list) -> list | None:

    """Проверяет значения и сохраняет новую запись с автоматическим ID."""
    if table_name not in metadata:
        raise TableNotFoundError(f"Таблица {table_name} не существует")

    table_data = load_table_data(table_name)

    if len(values) != len(metadata[table_name]["columns"]) - 1:
        raise ValueError("Неверное количество значений для вставки")

    new_row = {}
    for idx, value in enumerate(values, start=1):
        column_name = metadata[table_name]["columns"][idx]["name"]
        column_type = metadata[table_name]["columns"][idx]["type"]

        if type(value) is not TYPES_WHITELIST[column_type]:
            raise ValueError("Неверный тип данных для вставки")

        new_row[column_name] = value
    new_row["ID"] = max(
        (row["ID"] for row in table_data), default=0
    ) + 1

    table_data.append(new_row)

    save_table_data(table_name, table_data)

    print(f"Значения {values} успешно вставлены в"
            + f" таблицу {table_name} c ID = {new_row['ID']}")

    return table_data

@log_time
@handle_db_errors
def select(table_data: list[dict], where_clause: dict | None = None) -> list | None:
    """Возвращает все записи или записи, подходящие под условие."""
    if not where_clause:
        return table_data

    def f_comparison(row):
        return all(row[key] == value for key, value in where_clause.items())

    where_parts = [row for row in table_data if f_comparison(row)]

    return where_parts.copy()

@handle_db_errors
def update(table_data: list[dict], set_clause: dict, where_clause: dict) -> list | None:
    """Меняет указанные поля в записях, подходящих под условие."""
    where_parts = select.__wrapped__(table_data, where_clause)
    if where_parts is None:
        return None

    for row in where_parts:
        for key, value in set_clause.items():
            row[key] = value
    return table_data

@confirm_action("удалить запись")
@handle_db_errors
def delete(table_data: list[dict], where_clause: dict) -> list | None:
    """После подтверждения возвращает записи без подходящих под условие."""
    where_parts = select.__wrapped__(table_data, where_clause)
    if where_parts is None:
        return None
    copy_table = table_data.copy()

    for row in where_parts:
        copy_table.remove(row)

    return copy_table
