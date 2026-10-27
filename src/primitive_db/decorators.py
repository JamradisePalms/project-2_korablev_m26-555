import time
from functools import wraps
from json import JSONDecodeError

from .errors import ColumnNotFoundError, TableNotFoundError


def print_db_error(error):
    if isinstance(error, JSONDecodeError):
        print(f"Ошибка: Некорректный JSON-файл: {error}")
    elif isinstance(error, FileNotFoundError):
        print(f"Ошибка: Файл данных не найден: {error.filename}")
    elif isinstance(error, (TableNotFoundError, ColumnNotFoundError)):
        print(f"Ошибка: {error.args[0]}")
    elif isinstance(error, KeyError):
        print(f"Ошибка: Таблица или столбец {error} не найден")
    else:
        print(f"Ошибка валидации: {error}")


def handle_db_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (KeyError, ValueError, FileNotFoundError) as error:
            print_db_error(error)
            return None

    return wrapper


def confirm_action(action_name):

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"Вы действительно хотите выполнить {action_name}?")
            if input("[y/n]") == "y":
                return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        end_time = time.monotonic()
        print(f"Функция {func.__name__} выполнилась за" +
              f" {end_time - start_time:.3f} секунд")
        return result

    return wrapper

def create_cacher():
    cache = {}

    def cache_result(key, value_func):
        if key not in cache:
            result = value_func()
            if result is None:
                return None
            cache[key] = result
        return cache[key]

    return cache_result
