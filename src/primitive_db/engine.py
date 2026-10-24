import prompt

CMD_WHITELIST = {
    "exit" : "выйти из программы",
    "help": "справочная информация"
}


def print_allowed_commands() -> str:
    for cmd, desc in CMD_WHITELIST.items():
        print(f"<command> {cmd} - {desc}")

def welcome():
    print("Первая попытка запустить проект")
    print("***")
    print_allowed_commands()

    while True:
        cmd = prompt.string("Введите команду: ")
        if cmd == "exit":
            break
        elif cmd == "help":
            print_allowed_commands()
        else:
            print("Неизвестная команда")
