import sys
import os

# Получаем абсолютный путь к корневой директории проекта (autotests)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

import platform
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver
from selenium.webdriver.edge.webdriver import WebDriver as EdgeWebDriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from BaseUtils.configurations import config_reader


def is_windows() -> bool:
    """
    Проверка, является ли текущая ОС Windows.

    :return: True, если ОС Windows, иначе False.
    """
    return platform.system().lower() == "windows"


def create_driver(browser_name: str) -> WebDriver:
    """
    Создание экземпляра WebDriver на основе указанного браузера.

    :param browser_name: Название браузера (chrome, firefox, edge).
    :return: Экземпляр WebDriver для выбранного браузера.
    """
    if browser_name == "chrome":
        caps = DesiredCapabilities.CHROME.copy()  # Копия стандартных настроек для браузера
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}  # Добавляет настройки логирования производительности.

        options = ChromeOptions()
        options.add_experimental_option('prefs', {
            "download.prompt_for_download": False,  # Отключает запрос на подтверждение скачивания файла
            "download.directory_upgrade": True,  # Разрешает обновление директории загрузок
            "safebrowsing.enabled": True  # Включает безопасный просмотр.
        })
        # Устанавливает возможности для логирования производительности
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        if not is_windows():
            options.add_argument("--headless")  # Запуск браузера в headless-режиме
            options.add_argument("--window-size=1920,1080")  # Установка размера окна
        service = ChromeService(ChromeDriverManager().install())  # Установка ChromeDriver
        driver = ChromeWebDriver(service=service, options=options)  # Экземпляр WebDriver с настройками
    elif browser_name == "firefox":
        options = FirefoxOptions()
        if not is_windows():
            options.add_argument("--headless")  # Запуск браузера в headless-режиме
        service = FirefoxService(GeckoDriverManager().install())
        driver = FirefoxWebDriver(service=service, options=options)
    elif browser_name == "edge":
        options = EdgeOptions()
        if not is_windows():
            options.add_argument("--headless")  # Запуск браузера в headless-режиме
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver = EdgeWebDriver(service=service, options=options)
    else:
        raise ValueError(f"Unsupported browser: {browser_name}")

    return driver


def before_scenario() -> WebDriver:
    """
    Настройка WebDriver перед выполнением сценария.

    :return: Экземпляр WebDriver для взаимодействия с браузером.
    """
    browser_name = config_reader.read_configuration(
        category="basic info",
        key="browser"
    )
    driver = create_driver(browser_name)  # Полное создание WebDriver
    if is_windows():
        driver.maximize_window()
    return driver


def after_scenario(driver: WebDriver) -> None:
    """
    Завершение сценария и закрытие WebDriver.

    :param driver: Экземпляр WebDriver, который нужно закрыть.
    """
    driver.quit()
