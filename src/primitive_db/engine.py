import shlex
from pathlib import Path

import prompt
from prettytable import PrettyTable

from .core import create_table, delete, drop_table, insert, select, update
from .decorators import create_cacher, print_db_error
from .errors import ColumnNotFoundError, TableNotFoundError
from .parser import (
    parse_delete_command,
    parse_insert_command,
    parse_select_command,
    parse_update_command,
)
from .utils import load_metadata, load_table_data, save_metadata, save_table_data

CMD_WHITELIST = {
    "exit" : "выйти из программы",
    "help": "справочная информация",
    "create_table": "<имя_таблицы> <столбец1:тип> <столбец2:тип> .. - создать таблицу",
    "list_tables": "показать список всех таблиц",
    "drop_table": "<имя_таблицы> - удалить таблицу",
    "select": (
        'from <имя_таблицы> - прочитать все записи '
        '[where <столбец> = <значение>] - прочитать записи по условию.'
    ),
    "insert": (
        'into <имя_таблицы> values (<значение1>, <значение2>, ...) - '
        'создать запись'
    ),
    "update": (
        '<имя_таблицы> set <столбец> = <значение> '
        'where <столбец_условия> = <значение_условия> - обновить запись'
    ),
    "delete": (
        'from <имя_таблицы> where <столбец_условия> = <значение_условия> '
        '- удалить запись'
    ),
    "info": "<имя_таблицы> - показать информацию о таблице"
}


def print_allowed_commands() -> str:
    for cmd, desc in CMD_WHITELIST.items():
        print(f"<command> {cmd} - {desc}")

def welcome():
    """
        Legacy entrypoint
    """
    print_allowed_commands()

    while True:
        cmd = prompt.string("Введите команду: ")
        if cmd == "exit":
            break
        elif cmd == "help":
            print_allowed_commands()
        else:
            print(f"Функции <{cmd}> нет. Попробуйте снова")

def validate_clause(columns: list[dict], clause: dict) -> None:
    types = {"int": int, "str": str, "bool": bool}
    schema = {column["name"]: column["type"] for column in columns}
    for name, value in clause.items():
        if name not in schema:
            raise ColumnNotFoundError(f"Неизвестный столбец: {name}")
        if type(value) is not types[schema[name]]:
            raise ValueError(f"Неверный тип значения для столбца {name}")


def run():
    print("***Процесс работы с БД***")
    print_allowed_commands()

    cacher = create_cacher()

    metadata_path = Path("metadata.json")

    while True:
        user_input = prompt.string("Введите команду: ")

        try:
            args = shlex.split(user_input)
        except ValueError as error:
            print(f"Некорректное значение: {error}. Попробуйте снова.")
            continue

        if not args:
            continue

        cmd = args[0]

        if cmd not in CMD_WHITELIST:
            print(f"Функции <{cmd}> нет. Попробуйте снова")
            continue

        if cmd not in ("exit", "help"):
            try:
                updated_metadata = load_metadata(metadata_path)
            except (KeyError, ValueError, FileNotFoundError) as error:
                print_db_error(error)
                continue

        if cmd == "exit":
            break
        elif cmd == "help":
            print_allowed_commands()
        elif cmd == "create_table":
            if len(args) < 3:
                print("Недостаточно аргументов для создания таблицы")
                continue

            table_name = args[1]
            columns = args[2:]

            try:
                result = create_table(updated_metadata, table_name, columns)
                if result is None:
                    continue
                updated_metadata = result
                save_table_data(table_name, [])
                save_metadata(metadata_path, updated_metadata)
            except (KeyError, ValueError, FileNotFoundError) as error:
                print_db_error(error)

        elif cmd == "list_tables":
            for table_name in updated_metadata:
                print(table_name)

        elif cmd == "drop_table":
            if len(args) < 2:
                print("Недостаточно аргументов для удаления таблицы")
                continue

            table_name = args[1]

            try:
                result = drop_table(updated_metadata, table_name)
                if result is None:
                    continue
                updated_metadata = result
                save_metadata(metadata_path, updated_metadata)
                cacher = create_cacher()
            except (KeyError, ValueError, FileNotFoundError) as error:
                print_db_error(error)
        elif cmd == "select":
            try:
                table_name, where_clause = parse_select_command(user_input)
                if table_name not in updated_metadata:
                    raise TableNotFoundError(f"Таблица {table_name} не существует")

                columns = updated_metadata[table_name]["columns"]
                column_names = [column["name"] for column in columns]
                if where_clause:
                    validate_clause(columns, where_clause)

                rows = cacher(
                    user_input,
                    lambda: select(load_table_data(table_name), where_clause),
                )
                if rows is None:
                    continue
                table = PrettyTable()
                table.field_names = column_names
                table.add_rows([
                    [row[name] for name in column_names]
                    for row in rows
                ])
                print(table)
            except (KeyError, ValueError, FileNotFoundError) as error:
                print_db_error(error)
        elif cmd == "insert":
            try:
                table_name, values = parse_insert_command(user_input)
                if table_name not in updated_metadata:
                    raise TableNotFoundError(f"Таблица {table_name} не существует")
                result = insert(updated_metadata, table_name, values)
                if result is not None:
                    cacher = create_cacher()
            except (KeyError, ValueError, FileNotFoundError) as error:
                print_db_error(error)
        elif cmd == "update":
            try:
                table_name, set_clause, where_clause = parse_update_command(user_input)
                if table_name not in updated_metadata:
                    raise TableNotFoundError(f"Таблица {table_name} не существует")
                columns = updated_metadata[table_name]["columns"]
                validate_clause(columns, set_clause)
                validate_clause(columns, where_clause)
                if "ID" in set_clause:
                    raise ValueError("Изменять ID записи нельзя")

                table_data = load_table_data(table_name)
                table_data = update(table_data, set_clause, where_clause)
                if table_data is None:
                    continue
                save_table_data(table_name, table_data)
                cacher = create_cacher()
                print("Обновление выполнено успешно")
            except (KeyError, ValueError, FileNotFoundError) as error:
                print_db_error(error)
        elif cmd == "delete":
            try:
                table_name, where_clause = parse_delete_command(user_input)
                if table_name not in updated_metadata:
                    raise TableNotFoundError(f"Таблица {table_name} не существует")
                validate_clause(updated_metadata[table_name]["columns"], where_clause)

                table_data = load_table_data(table_name)
                remaining_rows = delete(table_data, where_clause)
                if remaining_rows is None:
                    continue
                save_table_data(table_name, remaining_rows)
                cacher = create_cacher()
                print(f"Удалено записей: {len(table_data) - len(remaining_rows)}")
            except (KeyError, ValueError, FileNotFoundError) as error:
                print_db_error(error)
        elif cmd == "info":
            try:
                if len(args) != 2:
                    raise ValueError("Ожидается: info <таблица>")
                table_name = args[1]
                if table_name not in updated_metadata:
                    raise TableNotFoundError(f"Таблица {table_name} не существует")

                columns = updated_metadata[table_name]["columns"]
                description = ", ".join(
                    f"{column['name']}:{column['type']}" for column in columns
                )
                table_data = load_table_data(table_name)
                print(f"Таблица: {table_name}")
                print(f"Столбцы: {description}")
                print(f"Количество записей: {len(table_data)}")
            except (KeyError, ValueError, FileNotFoundError) as error:
                print_db_error(error)
