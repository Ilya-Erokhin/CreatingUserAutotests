import os
import time
import requests

import re
import allure
import platform
from typing import Tuple, List


from BaseUtils.utils.logger import logger
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException, NoAlertPresentException, StaleElementReferenceException,
)
from selenium.webdriver.support.select import Select

from BaseUtils.configurations.config_reader import read_configuration
from BaseUtils.utils.switch_iframe_context import SwitchIframeContext

from BaseUtils.utils.wait_utils import WaitUtils


class CustomAssertionError(AssertionError):
    """Исключение для принудительной отметки шага как failed в Allure."""
    pass


class BasePage:
    """
    Класс для описания общих методов для всех последующих страниц.
    """

    def __init__(self, driver: WebDriver) -> None:
        """
        Инициализация объекта BasePage.

        Args:
            driver (WebDriver): Экземпляр WebDriver для Selenium.
        """
        self.driver = driver
        self.actions = ActionChains(self.driver)
        self.base_url = read_configuration(
            category="basic info",
            key="base_url"
        )
        self.locator_map = {
            "id": By.ID,
            "name": By.NAME,
            "class_name": By.CLASS_NAME,
            "link_text": By.LINK_TEXT,
            "xpath": By.XPATH,
            "css": By.CSS_SELECTOR
        }
        self.wait_utils = WaitUtils(
            driver,
            self.get_locator,
            self.get_element,
            self.take_screenshot_when_error_and_scroll
        )

    def get_locator(self, locator_type: str, locator_value: str) -> Tuple[str, str]:
        """
        Получение кортежа с локатором для поиска элемента в Selenium.

        Args:
            locator_type (str): Тип локатора (например, "id", "xpath").
            locator_value (str): Значение локатора.

        Returns:
            Tuple[str, str]: Кортеж с типом и значением локатора.
        """
        try:
            if locator_type not in self.locator_map:
                raise ValueError(f"Неподдерживаемый Тип Локатора: {locator_type}")
            return self.locator_map[locator_type], locator_value
        except Exception as e:
            logger.error(f"Ошибка при получении локатора: {e}")
            raise e

    def get_element(
            self,
            locator_type: str,
            locator_value: str,
            list_of_elements: bool = False,
    ) -> WebElement | List[WebElement]:
        """
        Находит и возвращает элемент на странице по заданному локатору и его значению.

        Args:
            locator_type (str): Тип локатора (например, "id", "xpath").
            locator_value (str): Значение локатора.
            list_of_elements (bool): Нужно ли вернуть СПИСОК всех элементов?

        Returns:
            WebElement или List[WebElement]: Элемент веб-страницы или список элементов.

        Raises:
            NoSuchElementException: Если элемент не найден на странице.
            ValueError: Если тип локатора не поддерживается.
        """
        try:
            element_locator: Tuple[str, str] = self.get_locator(locator_type, locator_value)
            if list_of_elements:
                # Возвращаем список элементов
                return self.driver.find_elements(*element_locator)
            else:
                # Возвращаем один элемент
                return self.driver.find_element(*element_locator)
        except (NoSuchElementException, TimeoutException, Exception) as e:
            error_message = (
                f'Элемент с локатором: "{locator_type}" \n'
                f'И значением: "{locator_value}" \n'
                f"НЕ НАЙДЕН на странице с помощью метода find_element-s: \n\n"
                f"{e}"
            )
            logger.error(error_message)
            raise e

    @allure.step('Клик на элемент с локатором: "{locator_type}" и значением: "{locator_value}"')
    def click_on_element(self, locator_type: str, locator_value: str) -> bool:
        """
        Выполняет клик по элементу на странице.

        Args:
            locator_type (str): Тип локатора (например, "id", "xpath").
            locator_value (str): Значение локатора.
        """
        try:
            current_url = self.driver.current_url
        except Exception:
            current_url = "Нового окна браузера"
        if self.wait_utils.wait_for_element_to_be_visible(locator_type, locator_value) or \
                self.wait_utils.wait_for_element_to_be_clickable(locator_type, locator_value):
            try:
                element = self.get_element(locator_type, locator_value)
                element.click()
                log = (
                    f'Клик на элемент: \n'
                    f'С локатором: "{locator_type}" \n'
                    f'и значением: "{locator_value}" \n'
                    f'На странице: {current_url}\n'
                )
                logger.info(log)
                allure.attach(
                    name="Успешный клик",
                    body=f"{log}"
                         f"Выполнен УСПЕШНО",
                    attachment_type=allure.attachment_type.TEXT
                )
                return True
            except (TimeoutException, ElementNotInteractableException, ElementClickInterceptedException) as e:
                # Попытка прокрутки до элемента
                try:
                    self.scroll_to_element(locator_type, locator_value)
                except Exception as scroll_exception:
                    error_message = (f"Ошибка при прокрутке до элемента: \n"
                                     f"{scroll_exception}")
                    self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
                    assert False, error_message
                # Если возникли исключения, попробуем выполнить клик с использованием JavaScript
                try:
                    # Прокручиваем к элементу перед выполнением JavaScript-клика
                    self.scroll_to_element(locator_type, locator_value)
                    element = self.get_element(locator_type, locator_value)
                    self.driver.execute_script("arguments[0].click();", element)
                    log = (
                        f'Клик на элемент: \n '
                        f'С локатором: "{locator_type}" \n'
                        f'и значением: "{locator_value}" \n'
                        f'Выполнен с использованием JavaScript \n'
                        f'На странице: "{current_url}" \n'
                    )
                    logger.info(log)
                    allure.attach(
                        name="Клик с использованием JavaScript",
                        body=log,
                        attachment_type=allure.attachment_type.TEXT
                    )
                    return True
                except Exception as js_click_exception:
                    error_message = (
                        f"Ошибка при клике на элемент с использованием JavaScript: \n"
                        f"{js_click_exception} \n")
                    logger.error(error_message)
                    allure.attach(
                        name="Ошибка при клике с использованием JavaScript",
                        body=error_message,
                        attachment_type=allure.attachment_type.TEXT
                    )
                    self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
                    assert False, error_message
            except Exception as e:
                error_message = (
                    f"Финальная ошибка при клике на элемент: \n"
                    f'С локатором: "{locator_type}" \n'
                    f'И значением: "{locator_value}" \n'
                    f"Ошибка: {e} \n"
                )
                logger.error(error_message)
                allure.attach(
                    name="Финальная ошибка при клике на элемент",
                    body=error_message,
                    attachment_type=allure.attachment_type.TEXT
                )
                self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
                assert False, error_message
        else:
            error_message = (
                f'Элемент: \n'
                f'С локатором: "{locator_type}" \n'
                f'и значением: "{locator_value}" \n'
                f'НЕ ВИДЕН или НЕ КЛИКАБЕЛЕН \n'
            )
            logger.error(error_message)
            allure.attach(
                name="Ошибка видимости/кликабельности элемента",
                body=error_message,
                attachment_type=allure.attachment_type.TEXT
            )
            assert False, error_message

    @allure.step(
        'Ввод текста: "{text_to_enter}" в элемент с локатором: "{locator_type}" и значением: "{locator_value}"')
    def type_into_element(
            self,
            locator_type: str,
            locator_value: str,
            text_to_enter: str,
            timeout: int = 5,
    ) -> bool:
        """
        Вводит текст в указанный элемент на странице.

        Args:
            locator_type (str): Тип локатора (например, "id", "xpath").
            locator_value (str): Значение локатора.
            text_to_enter (str): Текст для ввода.
            timeout (int): Таймаут ожидания
        """
        try:
            current_url = self.driver.current_url
        except Exception:
            current_url = "Нового окна браузера"
        if self.wait_utils.wait_for_element_to_be_visible(
                locator_type, locator_value, timeout=timeout) is True:
            element = self.get_element(locator_type, locator_value)
            try:
                try:
                    # Очистка с помощью JavaScript
                    self.driver.execute_script("arguments[0].value = '';", element)
                except Exception:
                    # Очистка с помощью Selenium
                    element.clear()
                element.send_keys(text_to_enter)
                log_info = (
                    f'Введен текст "{text_to_enter}" в элемент: \n'
                    f'C локатором: "{locator_type}" \n'
                    f'И значением: "{locator_value}" \n'
                    f'На странице: "{current_url}" \n'
                )
                logger.info(log_info)
                allure.attach(
                    name="Успешный ввод текста",
                    body=log_info,
                    attachment_type=allure.attachment_type.TEXT
                )
                return True
            except Exception as e:
                error_message = (
                    f'Ошибка при вводе текста "{text_to_enter}" в элемент: \n'
                    f'C локатором: "{locator_type}" \n'
                    f'И значением: "{locator_value}" \n'
                    f'На странице: "{current_url}" \n'
                    f"{e}")
                logger.error(error_message)
                allure.attach(
                    body=error_message,
                    name="ОШИБКА",
                    attachment_type=allure.attachment_type.TEXT
                )
                self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
                assert False, error_message
        else:
            error_message = (
                f'ОШИБКА ВИДИМОСТИ элемента \n'
                f'При попытке ввода текста: "{text_to_enter}" \n'
                f'Элемент с локатором: "{locator_type}" \n'
                f'И значением: "{locator_value}"\n'
                f'НЕ ВИДЕН странице: "{current_url}" \n'
            )
            logger.error(error_message)
            assert False, error_message

    def navigate_to_url(
            self,
            base_url: str | None = None,
            endpoint: str | None = None
    ) -> str:
        """
        Переходит по URL страницы или его конкретный эндпоинт.

        Args:
            base_url (str, optional): Базовый URL. По умолчанию None.
            endpoint (str, optional): Эндпоинт для добавления к базовому URL. По умолчанию None.
        """
        if base_url is None:
            base_url = self.base_url

        url_to_open = base_url + endpoint if endpoint else base_url

        with allure.step(f"Переход по URL: {url_to_open}"):
            logger.info(f"Переход по URL: {url_to_open} \n")
            if not url_to_open.startswith("http"):
                raise ValueError(f"Некорректный URL: {url_to_open}")
            self.driver.get(url=url_to_open)
        return url_to_open

    def scroll_to_element(self, locator_type: str, locator_value: str) -> None:
        """
        Прокручивает страницу к элементу с указанным локатором, используя различные методы прокрутки.

        Args:
            locator_type (str): Тип локатора (например, "id", "xpath").
            locator_value (str): Значение локатора.
        """
        element = self.get_element(locator_type, locator_value)
        success = False  # Флаг для отслеживания успешной прокрутки

        # Метод 1: JavaScript scrollIntoView
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            logger.info(
                f'Успешная прокрутка к элементу через JS скрипт scrollIntoView: \n'
                f'Элемент с локатором: "{locator_type}" \n'
                f'И значением: "{locator_value}"\n'
                f'Стал успешно ВИДЕН'
            )
            success = True
        except Exception as js_e:
            logger.warning(
                f"\n Не удалось прокрутить через JS скрипт scrollIntoView: \n"
                f"{js_e} \n"
            )

        # Метод 2: Actions
        if not success:
            try:
                self.actions.move_to_element(element).perform()
                logger.info(
                    f"\nУспешная прокрутка к элементу через ActionChains: \n"
                    f'Элемент с локатором: "{locator_type}" \n'
                    f'И значением: "{locator_value}"\n'
                    f'Стал успешно ВИДЕН'
                )
                success = True
            except Exception as actions_e:
                logger.warning(
                    f"\n Не удалось прокрутить через ActionChains: \n"
                    f"{actions_e} \n"
                )

        # Метод 3: Прокрутка по координатам элемента
        if not success:
            try:
                element_location = element.location_once_scrolled_into_view
                self.driver.execute_script(
                    "window.scrollTo(arguments[0], arguments[1]);",
                    element_location['x'], element_location['y']
                )
                logger.info(
                    f"\nУспешная прокрутка к элементу по координатам через JavaScript: \n"
                    f'Элемент с локатором: "{locator_type}" \n'
                    f'И значением: "{locator_value}"\n'
                    f'Стал успешно ВИДЕН'
                )
                success = True
            except Exception as coords_e:
                logger.warning(
                    f"\nНе удалось прокрутить к элементу по координатам через JavaScript: "
                    f"\nОШИБКА: {coords_e} \n"
                )

        if not success:
            error_message = (
                f"ОШИБКА - НИ ОДИН ИЗ СПОСОБОВ ПРОКРУТКИ К ЭЛЕМЕНТУ НЕ СРАБОТАЛ!"
                f"Ошибка при прокрутке страницы к элементу: \n"
                f'С локатором: "{locator_type}" \n'
                f'И значением: "{locator_value}"\n'
            )
            logger.error(error_message)
            allure.attach(
                name="ОШИБКА",
                body=error_message,
                attachment_type=allure.attachment_type.TEXT
            )
            self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
            assert False, error_message

    @allure.step("Выбор элемента из выпадающего списка по тексту: {option_text}")
    def select_from_dropdown(
            self,
            locator_type: str,
            locator_value: str,
            option_text: str,
            timeout: int = 5
    ) -> bool:
        """
        Выбор элемента из выпадающего списка по тексту.
        Если первый метод не удается, выполняется повторная попытка с нормализацией пробелов.

        Args:
            locator_type (str): Тип локатора (например, "id", "xpath").
            locator_value (str): Значение локатора.
            option_text (str): Текст для выбора.
            timeout (int): Таймаут ожидания.
        """
        try:
            # Шаг 1: Попытка выбора элемента по исходному тексту
            if self.wait_utils.wait_for_element_to_be_visible(
                    locator_type, locator_value, timeout=timeout) is True:
                dropdown_element = self.get_element(locator_type, locator_value)
                # Используем класс Select для работы с выпадающим списком
                select = Select(webelement=dropdown_element)
                try:
                    # Пробуем выбрать элемент по исходному тексту
                    select.select_by_visible_text(text=option_text)
                    log_first: str = (
                        f'Выбран элемент по тексту: "{option_text}" \n'
                        f'Из выпадающего списка'
                    )
                    logger.info(log_first)
                    allure.attach(
                        name="Успешный выбор элемента из выпадающего списка",
                        body=log_first,
                        attachment_type=allure.attachment_type.TEXT
                    )
                    return True
                except NoSuchElementException:
                    logger.warning(
                        f'Элемент с текстом: "{option_text}" \n '
                        f'НЕ НАЙДЕН, пробуем с нормализацией пробелов через метод strip()'
                    )

                    # Шаг 2: Попытка выбора с нормализованным текстом
                    normalized_text = option_text.strip()
                    try:
                        select.select_by_visible_text(text=normalized_text)
                        log_second: str = (
                            f'Выбран элемент по тексу: "{normalized_text}" \n'
                            f'С применением метода strip() для нормализации пробелов\n'
                            f'Из выпадающего списка \n'
                        )
                        logger.info(log_second)
                        allure.attach(
                            name="Успешный выбор элемента по тексту применением метода strip()",
                            body=log_second,
                            attachment_type=allure.attachment_type.TEXT
                        )
                        return True
                    except NoSuchElementException:
                        # Если стандартный метод не сработал, используем JS для поиска и клика по элементу
                        script = f"""
                            var options = arguments[0].getElementsByTagName('option');
                            for (var i = 0; i < options.length; i++) {{
                                if (options[i].textContent.trim() === '{normalized_text}') {{
                                    options[i].click();
                                    return;
                                }}
                            }}
                            throw 'Option not found';
                            """
                        self.driver.execute_script(script, dropdown_element)
                        allure.attach(
                            name='Выбор элемента с нормализованным текстом с использованием JavaScript',
                            body=f'Выбран элемент: "{normalized_text}" \n'
                                 f'Из выпадающего списка с использованием JavaScript',
                            attachment_type=allure.attachment_type.TEXT)
                        return True
        except (NoSuchElementException, TimeoutException, Exception) as e:
            error_message = (
                f"\nОшибка при попытке выбора элемента \n"
                f'По тексту: "{option_text}" \n'
                f"У выпадающего списка: \n"
                f'С локатором: "{locator_type}" \n'
                f'И значением: "{locator_value}" \n'
                f"{e} \n")
            logger.error(error_message)
            allure.attach(
                name="ОШИБКА выбора элемента по тексту",
                body=error_message,
                attachment_type=allure.attachment_type.TEXT)
            self.click_on_element(locator_type, locator_value)
            self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
            assert False, error_message

    @allure.step('Проверка текста элемента с локатором: "{locator_type}" и значением: "{locator_value}"')
    def assert_text_in_element(
            self,
            locator_type: str,
            locator_value: str,
            expected_full_text: str = None,
            at_least_text: str = None,
            timeout: int = 5,
            retry_attempts: int = 2,
            retry_delay: float = 1.0
    ) -> bool:
        """
        Проверяет, что указанный текст или его часть содержится в элементе на странице.

        Args:
            locator_type (str): Тип локатора (например, "id", "xpath").
            locator_value (str): Значение локатора.
            expected_full_text (str): Ожидаемый текст в элементе ЦЕЛИКОМ.
            at_least_text (str): ЧАСТЬ текста, которая должна присутствовать в элементе.
            timeout (int): Таймаут.
            retry_attempts (int): Количество повторных попыток при неудачной проверке текста.
            retry_delay (float): Задержка между попытками.
        Raises:
            AssertionError: Если текст в элементе не соответствует ожидаемому.
        """

        def normalize_text(text):
            """Убирает лишние пробелы и переносы строк."""
            return " ".join(text.split())

        actual_text = ""
        for attempt in range(retry_attempts):
            if self.wait_utils.wait_for_element_to_be_visible(
                    locator_type, locator_value, timeout=timeout) is True:
                try:
                    element = self.get_element(locator_type, locator_value)
                    try:
                        actual_text = element.text
                    except StaleElementReferenceException:
                        msg = (
                            "Повторная попытка получения текста элемента. \n"
                            "После получения исключения: StaleElementReferenceException"
                            f'Элемент с локатором: "{locator_type}" \n'
                            f'И значением: "{locator_value}" \n'
                            f'БЫЛ НЕАКТУАЛЕН. \n'
                            f'Повторная попытка его получения...'
                        )
                        logger.warning(msg)
                        allure.attach(
                            name="Повторная попытка получения текста элемента. \n",
                            body=msg
                        )
                        element = self.get_element(locator_type, locator_value)
                        actual_text = element.text

                    # Если текст пустой, делаем задержку и повторяем
                    if not actual_text:
                        logger.warning(
                            f"Текст элемента пуст. \n"
                            f"Попытка № {attempt + 1} из оставшихся {retry_attempts}."
                        )
                        allure.attach(
                            name=f"Неуспешная попытка № {attempt + 1} получения текста элемента",
                            body=f"Текст элемента ПУСТ. \n"
                                 f"Ожидание {retry_delay} секунд и повторяем попытку...",
                            attachment_type=allure.attachment_type.TEXT
                        )
                        time.sleep(retry_delay)
                        continue  # Переход к следующей попытке

                    # Нормализация текстов перед сравнением
                    normalized_actual_text = normalize_text(actual_text)
                    if expected_full_text:
                        normalized_expected_full_text = normalize_text(expected_full_text)
                        assert normalized_actual_text == normalized_expected_full_text, (
                            f'Ожидаемый текст ЦЕЛИКОМ: "{normalized_expected_full_text}" \n\n'
                            f"НЕ СООТВЕТСТВУЕТ \n\n"
                            f'Фактическому: "{normalized_actual_text}" \n\n'
                        )

                    if at_least_text:
                        normalized_at_least_text = normalize_text(at_least_text)
                        assert normalized_at_least_text in normalized_actual_text, (
                            f'ОЖИДАЕМАЯ ЧАСТЬ текста: "{normalized_at_least_text}" \n\n'
                            f"НЕ НАЙДЕНА В \n\n"
                            f'Фактическом полном тексте: "{normalized_actual_text}" \n\n'
                        )

                    log = (
                        f'Текст элемента: \n'
                        f'С локатором: "{locator_type}" \n'
                        f'и значением: "{locator_value}" \n'
                        f'Соответствует ожидаемому: "{expected_full_text or at_least_text}" \n'
                    )
                    logger.info(log)
                    allure.attach(
                        name="Успешная проверка текста элемента",
                        body=log,
                        attachment_type=allure.attachment_type.TEXT
                    )
                    return True
                except Exception as e:
                    error_message = (
                        f"Ошибка при проверке текста элемента: \n"
                        f'С локатором: "{locator_type}" \n'
                        f'И значением: "{locator_value}" \n'
                        f'Ожидаемый текст: "{expected_full_text or at_least_text}" \n\n'
                        f'Фактический текст: "{actual_text}" \n\n'
                        f"ОШИБКА: \n {e}"
                    )
                    logger.error(error_message)
                    allure.attach(
                        name="ФИНАЛЬНАЯ ОШИБКА проверки текста или его части внутри элемента.",
                        body=error_message,
                        attachment_type=allure.attachment_type.TEXT
                    )
                    self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
                    if attempt + 1 >= retry_attempts:
                        assert False, error_message
                    else:
                        logger.warning(
                            f"Попытка № {attempt + 1} из {retry_attempts} НЕ УДАЛАСЬ. \n"
                            f"Повторяем...\n"
                        )
                        time.sleep(retry_delay)

    @allure.step('Проверка текста элемента с локатором: "{locator_type}" и значением: "{locator_value}"')
    def assert_text_in_value_element(
            self,
            locator_type: str,
            locator_value: str,
            expected_text: str,
            timeout: int = 5,
    ) -> bool:
        """
        Проверяет, что указанный текст содержится в атрибуте value элемента на странице.

        Args:
            locator_type (str): Тип локатора (например, "id", "xpath").
            locator_value (str): Значение локатора.
            expected_text (str): Ожидаемый текст в элементе.
            timeout (str): Таймаут.

        Raises:
            AssertionError: Если текст в элементе не соответствует ожидаемому.
        """
        if self.wait_utils.wait_for_element_to_be_visible(locator_type, locator_value, timeout=timeout):
            try:
                try:
                    element = self.get_element(locator_type, locator_value)
                    # Первая попытка: проверка через атрибут value
                    actual_text_in_value = element.get_attribute("value")
                    if actual_text_in_value == expected_text:
                        log = (
                            f"Текст элемента:"
                            f'С локатором: "{locator_type}" \n'
                            f'и значением: "{locator_value}" \n'
                            f'Соответствует ожидаемому: "{expected_text}"'
                        )
                        logger.info(log)
                        allure.attach(
                            name='Успешная проверка текста элемента',
                            body=log,
                            attachment_type=allure.attachment_type.TEXT
                        )
                        return True

                    # Вторая попытка: проверка через JavaScript
                    script = "return arguments[0].value || arguments[0].innerText;"
                    actual_text_using_js = self.driver.execute_script(script, element)
                    assert expected_text in actual_text_using_js, \
                        (f'\n Ожидаемый текст: "{expected_text}" \n'
                         f'НЕ СООТВЕТСТВУЕТ \n'
                         f'Фактическому: "{actual_text_using_js}"')
                    log = (
                        f"\n Текст элемента:"
                        f'С локатором: "{locator_type}" \n'
                        f'и значением: "{locator_value}" \n'
                        f'Соответствует ожидаемому: "{expected_text}"'
                    )
                    logger.info(log)
                    allure.attach(
                        name='Успешная проверка текста элемента',
                        body=log,
                        attachment_type=allure.attachment_type.TEXT
                    )
                    return True

                except StaleElementReferenceException:
                    logger.warning("StaleElementReferenceException: элемент обновлен, повторная попытка...")
                    element = self.get_element(locator_type, locator_value)
                    actual_text_in_value = element.get_attribute("value")
                    if actual_text_in_value == expected_text:
                        log = (
                            f"\n Текст элемента:"
                            f'С локатором: "{locator_type}" \n'
                            f'и значением: "{locator_value}" \n'
                            f'Соответствует ожидаемому: "{expected_text}"'
                        )
                        logger.info(log)
                        allure.attach(
                            name='Успешная проверка текста элемента',
                            body=log,
                            attachment_type=allure.attachment_type.TEXT
                        )
                        return True
            except Exception as e:
                error_message = (
                    f"Ошибка при проверке текста элемента: \n"
                    f'С локатором: "{locator_type}" \n'
                    f'и значением: "{locator_value}" \n'
                    f'НИ ОДНА ИЗ ПОПЫТОК НЕ ПРОШЛА УСПЕШНО! \n'
                    f'ОШИБКА: \n {e} \n'
                )
                logger.error(error_message)
                allure.attach(
                    name="Финальная ОШИБКА при проверке текста элемента: ",
                    body=error_message,
                    attachment_type=allure.attachment_type.TEXT
                )
                self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
                assert False, error_message

    @allure.step('Проверка состояния чекбокса с локатором: "{locator_type}" и значением: "{locator_value}"')
    def is_checkbox_checked(self, locator_type: str, locator_value: str) -> bool:
        """
        Проверяет, отмечен ли чекбокс на странице.

        Args:
            locator_type (str): Тип локатора (например, "id", "xpath").
            locator_value (str): Значение локатора.
        Returns:
            bool: True, если чекбокс отмечен, False в противном случае.
        """
        try:
            element = self.get_element(locator_type, locator_value)
            checkbox_selected: bool = element.is_selected()
            if checkbox_selected:
                body = "ЧЕКБОКС - ОТМЕЧЕН"
            else:
                body = "ЧЕКБОКС - НЕ ОТМЕЧЕН"
            log: str = (
                f'Чекбокс с локатором: "{locator_type}" \n'
                f'и значением: "{locator_value}" \n'
                f'{body} \n'
            )
            logger.info(log)
            allure.attach(
                name="Проверка состояния чекбокса",
                body=log,
                attachment_type=allure.attachment_type.TEXT
            )
            return checkbox_selected
        except Exception as e:
            error_message = f"\nОшибка при проверке состояния чекбокса: \n {e}"
            logger.error(error_message)
            allure.attach(
                name="Ошибка",
                body=error_message,
                attachment_type=allure.attachment_type.TEXT
            )
            self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
            assert False, error_message

    @allure.step('Выставление галочки в чекбокс с локатором: "{locator_for_click}"')
    def tick_checkbox(
            self,
            locator_for_check: tuple,
            locator_for_click: tuple,
            turn_tick_on: bool = True
    ) -> None:
        """
        Выставление галочки в чекбокс.

        Args:
            locator_for_check (tuple): Локатор для проверки состояния чекбокса (<input>...etc.).
                                       Использовать локатор, который позволяет проверить,
                                            установлен ли флажок в чекбокс (атрибут "checked").
            locator_for_click (tuple): Локатор для клика по чекбоксу (<label>...etc.).
                                       Если для чекбокса доступен <label>, кликайте по нему, А НЕ ПО САМОМУ <input>!
            turn_tick_on (bool): Устанавливать (True) или снимать (False) галочку.

        :return: None
        """
        is_checked = self.is_checkbox_checked(*locator_for_check)

        if is_checked != turn_tick_on:
            self.click_on_element(*locator_for_click)
            assert self.is_checkbox_checked(*locator_for_check) is turn_tick_on
        else:
            allure.attach(
                name="ПРОПУСК ШАГА",
                body=f"Галочка элемента: \n"
                     f'С локатором: "{locator_for_click}" \n'
                     f"Уже была {'АКТИВИРОВАНА' if turn_tick_on else 'ДЕАКТИВИРОВАНА'}",
                attachment_type=allure.attachment_type.TEXT
            )
            self.take_screenshot_when_error_and_scroll(*locator_for_click)

    @allure.step('Проверка прикрепленного файла на странице')
    def check_pinned_file_on_page(
            self,
            locator_type: str,
            locator_value: str,
            file_name: str
    ) -> bool:
        """
        Проверка наличия и возможности скачивания прикрепленного PDF файла с электронной версией книги.

        :param locator_type: Тип локатора элемента (например, 'xpath', 'css', 'id' и т.д.)
        :param locator_value: Значение локатора элемента
        :param file_name: Ожидаемое имя файла (без размера и других дополнительных данных)
        :return: True, если файл найден и может быть скачан, иначе False
        """
        try:
            # Поиск элемента на странице
            element = self.driver.find_element(getattr(By, locator_type.upper()), locator_value)
            displayed_file_name = element.text
            logger.info(f'Отображаемое имя файла: "{displayed_file_name}" \n')
            allure.attach(name="Отображаемое имя файла", body=displayed_file_name,
                          attachment_type=allure.attachment_type.TEXT)

            # Удаляем все дополнительные данные из имени файла
            cleaned_displayed_file_name = re.sub(r'\s*\(\d+,\d+ МБ\)', '', displayed_file_name)
            logger.info(f"Очищенное отображаемое имя файла: '{cleaned_displayed_file_name}'")

            # Проверка соответствия имени файла
            if cleaned_displayed_file_name.strip() != file_name:
                error_message = (f'Ожидаемое имя файла: "{file_name}", \n'
                                 f'НЕ СООТВЕТСТВУЕТ \n'
                                 f'Фактическому имени файла: "{cleaned_displayed_file_name}" \n')
                logger.error(error_message)
                allure.attach(name="Несоответствие имени файла", body=error_message,
                              attachment_type=allure.attachment_type.TEXT)
                self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
                assert False, error_message

            # Получение URL файла
            file_url = element.get_attribute("href")
            logger.info(f"URL файла: '{file_url}' \n")

            # Проверка доступности файла по URL
            response = requests.head(file_url)
            if response.status_code != 200:
                error_message = (f"Файл не доступен для скачивания. \n"
                                 f'HTTP статус код: "{response.status_code}" \n')
                logger.error(error_message)
                allure.attach(name="Ошибка доступности файла", body=error_message,
                              attachment_type=allure.attachment_type.TEXT)
                assert False, error_message
            # Клик по элементу
            self.click_on_element(locator_type, locator_value)
            # Определение пути к директории загрузок
            if platform.system() == "Windows":
                download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            else:
                download_dir = os.getcwd()  # Используем текущую директорию на Unix-подобных системах

            # Проверка существования директории
            if not os.path.exists(download_dir):
                error_message = f'Директория "{download_dir}" НЕ СУЩЕСТВУЕТ. \n'
                logger.error(error_message)
                allure.attach(
                    name="Ошибка директории",
                    body=error_message,
                    attachment_type=allure.attachment_type.TEXT
                )
                assert False, error_message

            logger.info(f'\n Ожидание начала загрузки в директории: "{download_dir}" \n')
            download_started = self.wait_utils.wait_for_download_to_start(download_dir, file_name)

            if download_started:
                allure.attach(
                    name="Статус загрузки файла",
                    body=f'Файл: "{file_name}" скачивается ...',
                    attachment_type=allure.attachment_type.TEXT
                )
                logger.info(f'\n Файл: "{file_name}" успешно скачивается. \n')

                # Удаление файла после успешного скачивания
                file_path = os.path.join(download_dir, file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f'\n Файл: "{file_name}" успешно удален. \n')
                else:
                    logger.warning(f'\n Файл: "{file_name}" НЕ найден для удаления. \n')
                return True
            else:
                error_message = ("\n Ошибка при попытке скачивания файла: \n"
                                 "Загрузка НЕ началась \n")
                logger.error(error_message)
                allure.attach(name="Ошибка загрузки",
                              body=error_message, attachment_type=allure.attachment_type.TEXT)
                assert False, error_message
        except Exception as e:
            error_message = f"Неожиданная ошибка: {str(e)}"
            logger.error(error_message)
            allure.attach(name="Неожиданная ошибка",
                          body=error_message, attachment_type=allure.attachment_type.TEXT)
            self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
            assert False, error_message

    @allure.step('Сравнение текущего URL с ожидаемым URL: {expected_url}')
    def assert_current_url_expected_url(
            self,
            expected_url: str | None,
            check_only_part_of_url: bool = False
    ) -> bool:
        """
        Сравнение текущего URL с ожидаемым URL
        :param expected_url: Ожидаемый URL для сравнения
        :param check_only_part_of_url: Для возможности сравнить что в текущем URL есть определенная часть
        :return: bool в случае если URL совпадают, иначе False
        """
        current_url: str = self.driver.current_url

        if check_only_part_of_url:
            comparison = expected_url in current_url
            allure.attach(
                name="Проверка только статичной ЧАСТИ URL",
                body=f"В связи с динамически изменяемым текущим URL, -->\n"
                     f"производится проверка лишь его статичной части: \n"
                     f"{expected_url}",
                attachment_type=allure.attachment_type.TEXT
            )
            message = (
                f'\nОжидаемая часть в URL: "{expected_url}", \n'
                f"{'НАЙДЕНА В' if comparison else 'НЕ НАЙДЕНА В'} \n"
                f'Фактическом URL: "{current_url}" \n')
        else:
            comparison = current_url == expected_url
            message = (
                f'\nОжидаемый URL: "{expected_url}", \n'
                f"{'СООТВЕТСТВУЕТ' if comparison else 'НЕ СООТВЕТСТВУЕТ'} \n"
                f'Фактическому URL: "{current_url}" \n')

        logger.info(message)
        allure.attach(
            name="Сравнение URL",
            body=message,
            attachment_type=allure.attachment_type.TEXT
        )
        if not comparison:
            assert False, message

        return True

    @allure.step("Обработка всплывающего окна 'Alert'.")
    def accept_alert_window(self, accept: bool) -> bool:
        """
        Обрабатывает всплывающее окно (alert). Если accept_or_decline True, нажимает 'ОК', если False, 'Отмена'.

        :param accept: Если True, нажимает 'ОК'. Если False, нажимает 'Отмена'.
        :return: True, если операция прошла успешно; иначе False.
        """
        try:
            # Пытаемся переключиться на alert
            alert = self.driver.switch_to.alert
            if accept:
                alert.accept()
                action = "Окно подтверждено."
            else:
                alert.dismiss()
                action = "Окно отклонено."

            # Добавляем отчет Allure
            allure.attach(
                name="Результат действия с всплывающем окном на странице.",
                body=action,
                attachment_type=allure.attachment_type.TEXT
            )
            return True
        except NoAlertPresentException as no_alert:
            error_message = (
                f"Всплывающее окно НЕ НАЙДЕНО. \n"
                f"ОШИБКА NoAlertPresentException: \n"
                f"{no_alert}"
            )
            logger.error(error_message)
            allure.attach(
                name="ОШИБКА работы со всплывающем окном на странице.",
                body=error_message,
                attachment_type=allure.attachment_type.TEXT
            )
            assert False, error_message
        except Exception as e:
            error_message = f"Неизвестная ошибка: {str(e)}"
            logger.error(error_message)
            allure.attach(
                name="Ошибка работы с Alert",
                body=error_message,
                attachment_type=allure.attachment_type.TEXT
            )
            assert False, error_message

    def take_screenshot_when_error_and_scroll(
            self,
            locator_type: str | None = None,
            locator_value: str | None = None
    ) -> None:
        """
        Делает скриншот текущего окна браузера и прикрепляет его к отчету Allure.
        """
        if locator_type and locator_value:
            try:
                self.scroll_to_element(locator_type, locator_value)
            except Exception:
                pass

        screenshot = self.driver.get_screenshot_as_png()
        logger.info("\n Создан скриншот во время ошибки \n")
        with allure.step("Прикрепление скриншота во время ошибке"):
            allure.attach(
                name="Error Screenshot",
                body=screenshot,
                attachment_type=allure.attachment_type.PNG
            )

    @allure.step(
        'Проверка выбранного параметра: "{text_to_check}" в выпадающем списке элемента с локатором: "{locator_type}" и значением: "{locator_value}"')
    def check_selected_element_by_text(
            self,
            locator_type: str,
            locator_value: str,
            text_to_check: str
    ) -> bool:
        """
        Проверяет, что в выпадающем списке выбрано значение text_to_check.

        :param locator_type: Тип локатора (например, By.ID, By.CSS_SELECTOR).
        :param locator_value: Значение локатора для поиска элемента.
        :param text_to_check: Текст, который должен быть выбран в выпадающем списке.
        :return: True, если текст выбран правильно, иначе False.
        """
        # Найти элемент <select> по локатору
        element = self.get_element(locator_type, locator_value)
        select = Select(element)

        # Получить выбранный элемент
        selected_option: WebElement = select.first_selected_option

        # Получить текст выбранной опции
        selected_text: str = selected_option.text.strip()

        if selected_text == text_to_check:
            logger.info(f'\nВыбранный текст: "{selected_text}" в элементе \n'
                        f'С локатором: "{locator_type}" \n'
                        f'И значением: "{locator_value}" \n'
                        f'СООТВЕТСТВУЕТ ОЖИДАЕМОМУ: "{text_to_check}" \n')
            return True
        else:
            error_message = (
                f'\nОжидаемый текст выбранного элемента в выпадающем списке: "{text_to_check}" \n'
                f'НЕ СООТВЕТСТВУЕТ ВЫБРАННОМУ: "{selected_text}" \n'
            )
            logger.error(error_message)

            # Логирование ошибки в Allure
            allure.attach(
                error_message,
                name="НЕСООТВЕТСТВИЕ фактического выбранного элемента в выпадающем списке с ожидаемым!",
                attachment_type=allure.attachment_type.TEXT
            )
            assert False, error_message

    @allure.step(
        'Проверка наличия текста "{text_to_check}" в элементе с локатором: "{locator_type}" и значением: "{locator_value}"')
    def assert_text_in_dropdown(
            self,
            locator_type: str,
            locator_value: str,
            text_to_check: list
    ) -> bool:
        """
        Проверяет, что в выпадающем списке присутствуют значения из списка text_to_check.

        :param locator_type: Тип локатора (например, By.ID, By.CSS_SELECTOR).
        :param locator_value: Значение локатора для поиска элемента.
        :param text_to_check: Список текстов, которые должны быть найдены в выпадающем списке.
        :return: True, если все тексты найдены, иначе False.
        """
        try:
            # Найти элемент <select> по локатору
            element = self.get_element(locator_type, locator_value)
            select = Select(element)

            # Получаем все доступные опции в выпадающем списке
            options: list = [option.text.strip() for option in select.options]

            log_options: str = (
                f'Доступные опции в выпадающем списке: \n {options}'
            )
            logger.info(log_options)
            allure.attach(
                name="Все опции в текущем активном выпадающем списке:",
                body=log_options,
                attachment_type=allure.attachment_type.TEXT
            )
            # Проверяем наличие каждого текста из списка text_to_check в опциях
            for text in text_to_check:
                if text.strip() not in options:
                    none_text_in_options: str = (
                        f'Текст "{text}" НЕ НАЙДЕН в текущем выпадающем списке состоящем из:'
                        f' \n {options}'
                    )
                    logger.error(none_text_in_options)
                    allure.attach(
                        name='ОШИБКА - Переданный текст НЕ НАЙДЕН в текущем выпадающем списке!',
                        body=none_text_in_options,
                        attachment_type=allure.attachment_type.TEXT
                    )
                    assert False, (f'Текст "{text}" НЕ НАЙДЕН НЕ НАЙДЕН в текущем выпадающем списке!: '
                                   f'\n {options}')

            logger.info('Все переданные тексты УСПЕШНО НАЙДЕНЫ в выпадающем списке.')
            return True

        except Exception as e:
            error_log: str = f'ОШИБКА при проверке выпадающего списка: \n {str(e)}'
            logger.error(error_log)
            allure.attach(
                name='ОШИБКА при проверке выпадающего списка!',
                body=error_log,
                attachment_type=allure.attachment_type.TEXT)
            assert False, error_log

    def get_element_attribute(
            self,
            locator_type: str,
            locator_value: str,
            attribute: str
    ) -> str:
        """
        Возвращает значение атрибута указанного элемента.

        :param locator_type: Тип локатора (например, "xpath", "css selector", и т.д.)
        :param locator_value: Значение локатора для поиска элемента
        :param attribute: Имя атрибута, значение которого нужно получить
        :return: Значение атрибута элемента
        """
        element = self.get_element(locator_type, locator_value)
        return element.get_attribute(name=attribute)

    def assert_attribute_status_in_element(
            self,
            locator_type: str,
            locator_value: str,
            attribute: str,
            attr_value: str,
            positive: bool = True
    ) -> bool:
        """
        Проверяет наличие или отсутствие значения атрибута в элементе по локатору.

        :param locator_type: Тип локатора (например, XPath, CSS).
        :param locator_value: Значение локатора.
        :param attribute: Атрибут, значение которого нужно проверить.
        :param attr_value: Ожидаемое значение атрибута.
        :param positive: Если True, проверяет наличие значения; если False, отсутствие.
        :return: True, если проверка успешна.
        """
        status: str = self.get_element_attribute(locator_type, locator_value, attribute)
        condition_met = (attr_value in status) if positive else (attr_value not in status)

        log_message = (
            f'Атрибут "{attribute}" для элемента: \n'
            f'С локатором: "{locator_type} \n'
            f'И значением: {locator_value}" \n'
            f'{"содержит" if positive else "не содержит"} значение "{attr_value}". \n'
        )

        if condition_met:
            logger.info(log_message)
        else:
            error_message = f'Ожидаемое {"наличие" if positive else "отсутствие"} значения атрибута "{attr_value}" не выполнено.'
            logger.error(error_message)
            assert False, error_message

        allure.attach(
            name="Статус атрибута",
            body=f'Для локатора: "{locator_type}" \n'
                 f'И значения: "{locator_value}" \n'
                 f'Атрибут: "{attribute}" \n'
                 f'Статус атрибута: "{status}"',
            attachment_type=allure.attachment_type.TEXT
        )

        return True

    @allure.step('Проверка ссылки у элемента с локатором: {locator_link}')
    def full_check_link_on_page(
            self,
            locator_link: tuple,
            locator_elem_to_check: tuple,
            locator_elem_to_close_slider: tuple,
            text_to_assert: str
    ) -> None:
        """
        Проверяет ссылку на кликабельность и переходит по ней во временно окне.

        :param locator_link: Локатор для ссылки
        :param locator_elem_to_check: Локатор для элемента под проверку
        :param locator_elem_to_close_slider: Локатор для закрытия слайдера
        :param text_to_assert: Текст для проверки на временной странице
        """
        self.click_on_element(*locator_link)
        loc_type_check, loc_val_check = locator_elem_to_check
        with SwitchIframeContext(
                driver=self.driver,
                locator_type=loc_type_check,
                locator_value=loc_val_check
        ):
            try:
                self.assert_text_in_element(
                    *locator_elem_to_check,
                    expected_full_text=text_to_assert
                )
            except AssertionError:
                self.assert_text_in_value_element(
                    *locator_elem_to_check,
                    expected_text=text_to_assert
                )
            self.click_on_element(*locator_elem_to_close_slider)

    @allure.step('Поиск элементов в блоке по тексту: "{text_assert}"')
    def search_all_elems_contains_text(
            self,
            locator_type: str,
            locator_value: str,
            text_assert: str,
    ) -> int:
        """
        Ищет нужный текст в элементах и возвращает количество найденных элементов, содержащих текст.

        :param locator_type: Тип локатора (например, XPath, CSS).
        :param locator_value: Значение локатора.
        :param text_assert: Часть текста для проверки.
        :return: Количество найденных элементов, содержащих текст.
        """

        found_elem_count = 0
        errors = []

        try:
            # Получаем список элементов с помощью метода get_element
            elements: list = self.get_element(
                locator_type=locator_type,
                locator_value=locator_value,
                list_of_elements=True
            )

            # Проверяем каждый элемент на наличие искомого текста
            for elem in elements:
                try:
                    # Получаем текст текущего элемента
                    actual_text = elem.text
                    # Проверяем, содержится ли искомая часть текста в фактическом тексте
                    if text_assert in actual_text:
                        found_elem_count += 1
                    else:
                        errors.append(f'Текст "{text_assert}" не найден в элементе: "{actual_text}"')
                except StaleElementReferenceException:
                    errors.append(f"Ссылка на элемент устарела при проверке: {elem}")
                except Exception as e:
                    errors.append(f"Ошибка при проверке элемента: {str(e)}")
        except Exception as e:
            errors.append(f"Ошибка при получении элементов: {str(e)}")

        # Если были ошибки в процессе проверки, добавляем их в отчет
        if errors:
            error_message = "\n".join(errors)
            allure.attach(
                name="Ошибки поиска элементов",
                body=error_message,
                attachment_type=allure.attachment_type.TEXT
            )
            assert False, f"Обнаружены ошибки при проверке элементов: \n{error_message}"
        return found_elem_count

    @allure.step('Проверка всплывающего текста: "{text_assert}" при наведении на элемент')
    def assert_popup_text(
            self,
            locator_type: str,
            locator_value: str,
            text_assert: str,
    ):
        # Находим элемент с помощью метода get_element
        element_to_hover = self.get_element(locator_type, locator_value)

        # Наведение курсора на элемент с помощью ActionChains
        logger.info('Наведение курсора на элемент.')
        action = ActionChains(self.driver)
        action.move_to_element(element_to_hover).perform()

        # Получение ближайшего элемента li, который содержит атрибут title
        list_item = self.get_element(
            locator_type="xpath",
            locator_value=f"{locator_value}/ancestor::li"
        )
        actual_text = list_item.get_attribute('title')

        # Логирование полученного текста
        logger.info(f'Всплывающий текст элемента: {actual_text}')

        # Проверка текста с учетом пробелов и регистра
        assert text_assert.strip().lower() in actual_text.strip().lower(), (
            f'Ожидаемый текст: "{text_assert}" \n'
            f'НЕ НАЙДЕН во всплывающем тексте элемента.'
        )

    @allure.step('Проверка отсутствия текста: "{expected_absence_text}" на странице.')
    def absence_check(
            self,
            locator_type: str = None,
            locator_value: str = None,
            expected_absence_text: str = None
    ) -> bool:
        """
        Проверяет отсутствие заданного текста на странице или в элементе.
        Если locator_type и locator_value не указаны, проверяет всю страницу через JS.

        Args:
            locator_type (str): Тип локатора (например, "id", "xpath").
            locator_value (str): Значение локатора.
            expected_absence_text (str): Ожидаемый текст, который не должен быть на странице или в элементе.
        Returns:
            bool: True, если текст не найден, иначе False.
        """
        if locator_type and locator_value:
            element = self.get_element(locator_type, locator_value)
            actual_text = element.text
            if expected_absence_text in actual_text:
                self.take_screenshot_when_error_and_scroll()
                log_message = f'Текст "{expected_absence_text}" НАЙДЕН в элементе, хотя его не должно быть!'
                logger.error(log_message)
                allure.attach(
                    name='ОШИБКА: Найден запрещенный текст в элементе!',
                    body=log_message,
                    attachment_type=allure.attachment_type.TEXT
                )
                raise CustomAssertionError(log_message)
            else:
                log_by_locator = f'Текст "{expected_absence_text}" отсутствует, как и ожидалось.'
                logger.info(log_by_locator)
                allure.attach(
                    name="Успешная проверка ОТСУТСТВИЯ текста на странице.",
                    body=log_by_locator
                )
                return True
        else:
            page_source = self.driver.execute_script("return document.body.innerText;")
            if expected_absence_text in page_source:
                self.take_screenshot_when_error_and_scroll()
                log_message = f'Текст "{expected_absence_text}" НАЙДЕН на странице, хотя его не должно быть!'
                logger.error(log_message)
                allure.attach(
                    name='ОШИБКА: Найден запрещенный текст на странице!',
                    body=log_message,
                    attachment_type=allure.attachment_type.TEXT
                )
                raise CustomAssertionError(log_message)
            else:
                log_full_page = f'Текст "{expected_absence_text}" отсутствует на странице, как и ожидалось.'
                allure.attach(
                    name="Успешная проверка ОТСУТСТВИЯ текста на странице.",
                    body=log_full_page
                )
                logger.info(log_full_page)
                return True

    def try_to_find_errors_words(self):
        """
        Ищет критические слова на странице из предустановленного списка и логирует их при нахождении, не прерывая выполнение.
        """
        error_words = [
            "Error", "Timeout", "Abort",
            "Fail", "Failure", "Invalid",
            "Rejected", "Overflow", "Exception",
            "TypeError", "SystemException", "unknown",
        ]
        for error_word in error_words:
            self.absence_check(expected_absence_text=error_word)


