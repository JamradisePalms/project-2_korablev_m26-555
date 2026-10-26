import shlex


def parse_value(value: str) -> str | int | bool:
    value = value.strip()

    if not value:
        raise ValueError("Значение не задано")

    if value[0] in ("'", '"') and value[-1] == value[0] and len(value) >= 2:
        return value[1:-1]

    if value.lower() in ("true", "false"):
        return value.lower() == "true"

    try:
        return int(value)
    except ValueError:
        raise ValueError("Ожидается целое число, true/false или строка в кавычках")

def parse_where_state(state: str) -> dict[str, str | int | bool]:
    key, separator, value = state.partition("=")
    key = key.strip()

    if not separator or not key:
        raise ValueError("Ожидается условие вида: столбец = значение")

    return {key: parse_value(value)}


def parse_select_command(command: str) -> tuple[str, dict | None]:
    parts = command.split(maxsplit=3)
    if len(parts) < 3 or parts[:2] != ["select", "from"]:
        raise ValueError("Ожидается: select from <таблица> [where <условие>]")

    table_name = parts[2]
    where_clause = None
    if len(parts) == 4:
        condition = parts[3].split(maxsplit=1)
        if len(condition) != 2 or condition[0] != "where":
            raise ValueError("Ожидается: where <столбец> = <значение>")
        where_clause = parse_where_state(condition[1])

    return table_name, where_clause


def parse_insert_command(command: str) -> tuple[str, list]:
    parts = command.split(maxsplit=4)
    if (
        len(parts) != 5
        or parts[:2] != ["insert", "into"]
        or parts[3] != "values"
    ):
        raise ValueError("Ожидается: insert into <таблица> values (<значения>)")

    values_text = parts[4].strip()
    if not (values_text.startswith("(") and values_text.endswith(")")):
        raise ValueError("Значения должны быть заключены в круглые скобки")

    lexer = shlex.shlex(values_text[1:-1], posix=False, punctuation_chars=",")
    lexer.whitespace_split = True
    lexer.commenters = ""

    tokens = list(lexer)
    if not tokens or len(tokens) % 2 == 0:
        raise ValueError("Ожидаются значения, разделённые запятыми")
    if any(token != "," for token in tokens[1::2]):
        raise ValueError("Значения должны быть разделены запятыми")

    return parts[2], [parse_value(token) for token in tokens[::2]]

def parse_update_command(command: str) -> tuple[str, dict, dict]:
    lexer = shlex.shlex(command, posix=False, punctuation_chars="=,")
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = list(lexer)

    if (
        len(tokens) != 10
        or tokens[0] != "update"
        or tokens[2] != "set"
        or tokens[4] != "="
        or tokens[6] != "where"
        or tokens[8] != "="
    ):
        raise ValueError("Ожидается: update <таблица> set <условие> where <условие>")

    set_clause = {tokens[3]: parse_value(tokens[5])}
    where_clause = {tokens[7]: parse_value(tokens[9])}
    return tokens[1], set_clause, where_clause


def parse_delete_command(command: str) -> tuple[str, dict]:
    parts = command.split(maxsplit=3)
    if len(parts) != 4 or parts[:2] != ["delete", "from"]:
        raise ValueError("Ожидается: delete from <таблица> where <условие>")
    condition = parts[3].split(maxsplit=1)
    if len(condition) != 2 or condition[0] != "where":
        raise ValueError("Для delete необходимо условие where")
    return parts[2], parse_where_state(condition[1])
