import shlex

import prompt
from prettytable import PrettyTable

from .constants import CMD_WHITELIST, METADATA_PATH, TYPES_WHITELIST
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


def print_allowed_commands() -> str:
    """Печатает список команд и краткую справку."""
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
    """Проверяет имена столбцов и типы значений условия."""
    schema = {column["name"]: column["type"] for column in columns}
    for name, value in clause.items():
        if name not in schema:
            raise ColumnNotFoundError(f"Неизвестный столбец: {name}")
        if type(value) is not TYPES_WHITELIST[schema[name]]:
            raise ValueError(f"Неверный тип значения для столбца {name}")


def run():
    """Принимает команды, выполняет операции и выводит результаты."""
    print("***Процесс работы с БД***")
    print_allowed_commands()

    cacher, invalidate = create_cacher()


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

        try:
            if cmd not in ("exit", "help"):
                updated_metadata = load_metadata(METADATA_PATH)

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

                result = create_table(updated_metadata, table_name, columns)
                if result is None:
                    continue
                updated_metadata = result
                save_table_data(table_name, [])
                save_metadata(METADATA_PATH, updated_metadata)

            elif cmd == "list_tables":
                for table_name in updated_metadata:
                    print(table_name)

            elif cmd == "drop_table":
                if len(args) < 2:
                    print("Недостаточно аргументов для удаления таблицы")
                    continue

                table_name = args[1]

                result = drop_table(updated_metadata, table_name)
                if result is None:
                    continue
                updated_metadata = result
                save_metadata(METADATA_PATH, updated_metadata)
                invalidate(table_name)
            elif cmd == "select":
                table_name, where_clause = parse_select_command(user_input)
                if table_name not in updated_metadata:
                    raise TableNotFoundError(f"Таблица {table_name} не существует")

                columns = updated_metadata[table_name]["columns"]
                column_names = [column["name"] for column in columns]
                if where_clause:
                    validate_clause(columns, where_clause)

                key = (table_name, tuple(sorted((where_clause or {}).items())))
                rows = cacher(
                    key,
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
            elif cmd == "insert":
                table_name, values = parse_insert_command(user_input)
                if table_name not in updated_metadata:
                    raise TableNotFoundError(f"Таблица {table_name} не существует")
                result = insert(updated_metadata, table_name, values)
                if result is not None:
                    invalidate(table_name)
            elif cmd == "update":
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
                invalidate(table_name)
                print("Обновление выполнено успешно")
            elif cmd == "delete":
                table_name, where_clause = parse_delete_command(user_input)
                if table_name not in updated_metadata:
                    raise TableNotFoundError(f"Таблица {table_name} не существует")
                validate_clause(updated_metadata[table_name]["columns"], where_clause)

                table_data = load_table_data(table_name)
                remaining_rows = delete(table_data, where_clause)
                if remaining_rows is None:
                    continue
                save_table_data(table_name, remaining_rows)
                invalidate(table_name)
                print(f"Удалено записей: {len(table_data) - len(remaining_rows)}")
            elif cmd == "info":
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
