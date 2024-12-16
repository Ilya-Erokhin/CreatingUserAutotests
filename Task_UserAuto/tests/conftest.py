import sys
import os

import pytest
from selenium.webdriver.chrome.webdriver import WebDriver


# Получаем абсолютный путь к корневой директории проекта
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from Task_UserAuto.pages.creating_new_user_page import CreatingUser
from BaseUtils.configurations.config_reader import read_configuration
from BaseUtils.environment.environment import before_scenario, after_scenario
from BaseUtils.pages.login_page import LoginPage


@pytest.fixture(scope="function")
def driver() -> WebDriver:
    """
    Фикстура для инициализации и предоставления экземпляра WebDriver на время выполнения тестов в модуле.
    Подготовка выполняется перед запуском тестов, а завершение работы происходит после выполнения всех тестов в модуле.

    Возвращает:
        WebDriver: Экземпляр WebDriver.
    """
    # Инициализация WebDriver перед началом тестов
    driver = before_scenario()
    yield driver  # Передача WebDriver тестам
    after_scenario(driver)  # Завершение работы WebDriver после выполнения всех тестов в


@pytest.fixture(scope="function")
def authenticated_driver(driver, login_page):
    """
    Фикстура для аутентификации драйвера с использованием учетных данных.
    После успешной аутентификации предоставляет экземпляр аутентифицированного WebDriver.

    Аргументы:
        driver (WebDriver): Экземпляр WebDriver.
        login_page (LoginPage): Экземпляр страницы входа.

    Возвращает:
        WebDriver: Аутентифицированный экземпляр WebDriver.
    """
    username = read_configuration(
        category="credentials",
        key="login",
    )
    password = read_configuration(
        category="credentials",
        key="password",
    )
    login_page.login(username, password)
    yield driver


@pytest.fixture(scope="function")
def login_page(driver) -> LoginPage:
    """
    Фикстура для инициализации и предоставления экземпляра LoginPage.

    Аргументы:
        driver (WebDriver): Экземпляр WebDriver.

    Возвращает:
        LoginPage: Экземпляр LoginPage.
    """
    return LoginPage(driver)


@pytest.fixture(scope="function")
def creating_new_user_page(authenticated_driver) -> CreatingUser:
    """
    Фикстура для инициализации и предоставления экземпляра CreatingUser.

    Аргументы:
        authenticated_driver (WebDriver): Аутентифицированный экземпляр WebDriver.

    Возвращает:
        CreateNewBookPage: Экземпляр CreatingUser.
    """
    return CreatingUser(authenticated_driver)
