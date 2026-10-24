import shlex
from pathlib import Path

import prompt

from .core import create_table, drop_table
from .utils import load_metadata, save_metadata

CMD_WHITELIST = {
    "exit" : "выйти из программы",
    "help": "справочная информация",
    "create_table": "<имя_таблицы> <столбец1:тип> <столбец2:тип> .. - создать таблицу",
    "list_tables": "показать список всех таблиц",
    "drop_table": "<имя_таблицы> - удалить таблицу"
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

def run():
    print("***Процесс работы с БД***")
    print_allowed_commands()

    metadata_path = Path("metadata.json")

    while True:
        updated_metadata = load_metadata(metadata_path)
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
                updated_metadata = create_table(updated_metadata, table_name, columns)
                save_metadata(metadata_path, updated_metadata)
            except ValueError as e:
                print(e)

        elif cmd == "list_tables":
            for table_name in updated_metadata:
                print(table_name)

        elif cmd == "drop_table":
            if len(args) < 2:
                print("Недостаточно аргументов для удаления таблицы")
                continue

            table_name = args[1]

            try:
                updated_metadata = drop_table(updated_metadata, table_name)
                save_metadata(metadata_path, updated_metadata)
            except ValueError as e:
                print(e)


