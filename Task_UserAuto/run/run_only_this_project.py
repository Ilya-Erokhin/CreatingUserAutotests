#!/usr/bin/env python3

import subprocess


def run_command(command: list[str]) -> bool:
    """
    Выполнить команду в оболочке.

    Args:
        command (list[str]): Команда и её аргументы для выполнения.

    Returns:
        bool: True, если команда выполнена успешно, False в противном случае.
    """
    try:
        subprocess.run(command, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"The command {e.cmd} failed.")
        print(e.stdout)
        print(e.stderr)
        return False


if __name__ == "__main__":
    # Команда 1: Запуск pytest для создания отчета Allure
    if not run_command(["python", "-m", "pytest", "--alluredir=./report"]):
        print("pytest failed.")
        exit(1)  # Если ловим ошибку, завершаем с кодом 1 (ошибка)

    # Команда 2: Генерация отчета Allure
    if not run_command(["allure", "generate", "--clean", "./report", "-o", "allure-report"]):
        print("Error generating the Allure report.")
        exit(1)  # Если ловим ошибку, завершаем с кодом 1 (ошибка)

    # # Команда 3: Локальное поднятие сервера с отчетом Allure
    # if not run_command(["allure", "serve", "./report"]):
    #     print("Error run local Allure server")
    #     exit(1)  ## Если ловим ошибку, завершаем с кодом 1 (ошибка)

    # Команда 3: Комбинирование отчетов Allure (формируется complete.html внутри папки allure-report)
    if not run_command(["allure-combine", "./allure-report"]):
        print("Error combining the Allure reports.")
        exit(1)  # Если ловим ошибку, завершаем с кодом 1 (ошибка)

    print("All commands executed successfully.")
