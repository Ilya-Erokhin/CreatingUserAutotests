import configparser
import os


def read_configuration(category: str, key: str, project_dir: str | None = None) -> str:
    """
    Читает значение из конфигурационного файла config.ini.

    Извлекает значение по указанной категории и ключу из файла конфигурации config.ini,
    который находится в директории указанного проекта.

    :param category: Категория (секция) в конфигурационном файле.
    :param key: Ключ (параметр) в указанной категории, значение которого нужно получить.
    :param project_dir: Директория проекта, в которой находится конфигурационный файл.
    :return: Значение параметра из конфигурационного файла в виде строки.
    """
    # Определяем абсолютный путь к директории, в которой находится текущий файл config_reader.py
    current_file_dir = os.path.abspath(os.path.dirname(__file__))

    if project_dir:
        # Если передан project_dir, ищет config.ini в конкретном проекте
        config_file_path = os.path.join('..', project_dir, 'configurations', 'config.ini')
    else:
        # По умолчанию ищем config.ini в той же директории, что и config_reader.py
        config_file_path = os.path.join(current_file_dir, 'config.ini')

    # Приводим путь к абсолютному пути
    config_file_path = os.path.abspath(config_file_path)

    # Проверяем, существует ли файл config.ini
    if not os.path.isfile(config_file_path):
        raise FileNotFoundError(f"Файл config.ini НЕ найден по пути: {config_file_path}")

    # Создаем объект ConfigParser и читаем конфигурационный файл
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_file_path, encoding='utf-8')

    # Проверяем, существует ли секция и ключ, чтобы избежать ошибок
    if not config.has_section(category):
        raise configparser.NoSectionError(category)
    if not config.has_option(category, key):
        raise configparser.NoOptionError(key, category)

    return config.get(category, key)
