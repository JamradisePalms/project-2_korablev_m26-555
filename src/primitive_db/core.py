# Основная логика работы с таблицами и данными
TYPES_WHITELIST = {"int", "bool", "str"}

def create_table(metadata: dict, table_name: str, columns: list) -> dict:
    if table_name in metadata:
        raise ValueError(f"Ошибка: Таблица {table_name} уже существует")

    updated_columns = columns.copy()
    if "ID:int" not in columns:
        updated_columns.insert(0, "ID:int")

    for column in updated_columns:
        column_name, column_type = column.split(":")
        if column_type not in TYPES_WHITELIST:
            raise ValueError(f"Invalid column type: {column_type}")

    metadata[table_name] = {"columns": updated_columns}

    print(f"Таблица {table_name} успешно создана со столбцами: {updated_columns}")
    return metadata


def drop_table(metadata: dict, table_name: str) -> dict:
    copy_metadata = metadata.copy()

    if table_name not in copy_metadata:
        raise ValueError(f"Ошибка: Таблица {table_name} не существует")

    del copy_metadata[table_name]

    print(f"Таблица {table_name} успешно удалена")

    return copy_metadata
