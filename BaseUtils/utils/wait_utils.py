import os
import time
from typing import Tuple

import allure
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException
)
from BaseUtils.utils.logger import logger


class WaitUtils:
    def __init__(
            self,
            driver,
            get_locator,
            get_element,
            take_screenshot_when_error_and_scroll
    ):
        self.driver = driver
        self.get_locator = get_locator
        self.get_element = get_element
        self.take_screenshot_when_error_and_scroll = take_screenshot_when_error_and_scroll

    def _attach_debug_info_on_error(
            self,
            element_locator: WebElement | Tuple[str, str],
            timeout: int
    ) -> None:
        """
        Попытка найти элемент и прикрепить отладочную информацию.
        ----------
        Params:
        element_locator: Кортеж с типом и значением локатора элемента (например, (By.XPATH, '//div[@id="example"]')).
        timeout: Время ожидания элемента в секундах.
        """
        try:
            # Попробуй снова найти элемент
            element: WebElement = self.driver.find_element(*element_locator)
            element_state = {
                'displayed': element.is_displayed(),
                'enabled': element.is_enabled(),
                'text': element.text,
                'tag_name': element.tag_name
            }
            state_log = (
                f"\nСостояние элемента: {element_state}\n"
            )
            logger.error(state_log)

            # Прикрепляем состояние элемента к отчету
            allure.attach(
                name="Состояние элемента при ошибке",
                body=state_log,
                attachment_type=allure.attachment_type.TEXT
            )

            if not element.is_displayed():
                scroll_log = (
                    f'Элемент с локатором: "{element_locator}" \n'
                    f'НЕ ОТОБРАЖАЕТСЯ на странице. \n'
                    f'Попытка прокрутки к элементу. \n'
                )
                logger.error(scroll_log)
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable(mark=element_locator)
                )
        except NoSuchElementException:
            not_found_log = (
                f'Элемент c локатором: "{element_locator}" \n'
                'НЕ НАЙДЕН на странице для формирования детального состояния элемента методом _attach_debug_info_on_error\n'
            )
            logger.error(not_found_log)
        except Exception as e:
            error_log = f"\nОшибка при сборе отладочной информации: {e}\n"
            logger.error(error_log)
            allure.attach(
                name="Ошибка при сборе отладочной информации",
                body=error_log,
                attachment_type=allure.attachment_type.TEXT
            )

    @allure.step("Ожидание кликабельности элемента с локатором: {locator_type} и значением: {locator_value}")
    def wait_for_element_to_be_clickable(
            self,
            locator_type: str,
            locator_value: str,
            timeout: int = 5,
            max_retries: int = 5
    ) -> bool:
        """
            Ожидает, что элемент станет кликабельным, выполняя несколько попыток.

            Params:
            ----------
            locator_type : str
                Тип локатора (например, XPath, CSS_SELECTOR).
            locator_value : str
                Значение локатора для поиска элемента.
            timeout : int, по умолчанию 5
                Время ожидания в секундах для каждой попытки.
            max_retries : int, по умолчанию 5
                Максимальное количество попыток.
        """
        element_locator = self.get_locator(locator_type, locator_value)
        start_time = time.time()
        success = False

        for attempt in range(max_retries):
            try:
                # Ожидание видимости элемента
                WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located(element_locator)
                )
                # Ожидание кликабельности элемента
                WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable(element_locator)
                )
                success = True
                end_time = time.time()
                elapsed_time = end_time - start_time
                log: str = (
                    f'Элемент с локатором: "{locator_type}" \n'
                    f'и значением: "{locator_value}" \n'
                    f'Стал кликабельным! \n'
                    f"Время ожидания: {elapsed_time:.2f} секунд \n"
                )
                logger.info(log)
                allure.attach(
                    name="Ожидание кликабельности элемента",
                    body=log,
                    attachment_type=allure.attachment_type.TEXT
                )
                return True

            except StaleElementReferenceException:
                logger.warning(f"Попытка {attempt + 1}/{max_retries}: \n"
                               f"Элемент стал устаревшим")
                self._attach_debug_info_on_error(element_locator, timeout)
                continue

            except TimeoutException:
                logger.warning(f"Попытка {attempt + 1}/{max_retries}: \n"
                               f"Таймаут ожидания кликабельности")
                self._attach_debug_info_on_error(element_locator, timeout)
                continue

            except Exception as e:
                end_time = time.time()
                elapsed_time = end_time - start_time
                error_message: str = (
                    f"Ошибка ожидания кликабельности элемента: \n"
                    f'С локатором: "{locator_type}" \n'
                    f'и значением: "{locator_value}" \n'
                    f"Время ожидания: {elapsed_time:.2f} секунд"
                )
                logger.error(f"{error_message}. \n"
                             f"Ошибка: {e}")
                allure.attach(
                    name="Exception",
                    body=error_message,
                    attachment_type=allure.attachment_type.TEXT
                )
                self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
                success = False  # Если исключение, устанавливаем флаг успеха в False
                break  # Прерываем цикл, если возникла непредвиденная ошибка

        # Если ни одна попытка не была успешной, роняем тест
        if not success:
            self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
            end_time = time.time()
            elapsed_time = end_time - start_time
            error_message: str = (
                f"\nТаймаут ожидания кликабельности элемента после {max_retries} попыток: \n"
                f'С локатором: "{locator_type}" \n'
                f'и значением: "{locator_value}" \n'
            )
            logger.error(error_message)
            self._attach_debug_info_on_error(element_locator, timeout)
            allure.attach(
                name="Timeout Error",
                body=f"{error_message}\n"
                     f"Время ожидания: {elapsed_time:.2f} секунд",
                attachment_type=allure.attachment_type.TEXT)
            assert False, error_message

    @allure.step("Ожидание видимости элемента с локатором: {locator_type} и значением: {locator_value}")
    def wait_for_element_to_be_visible(
            self,
            locator_type: str,
            locator_value: str,
            timeout: int = 5,
            return_elem: bool = False
    ) -> bool | WebElement:
        """
        Ожидает, что элемент станет видимым с помощью Selenium или JavaScript-проверки.

        Params:
        ----------
        locator_type : str
            Тип локатора (например, XPath, CSS_SELECTOR).
        locator_value : str
            Значение локатора для поиска элемента.
        timeout : int, по умолчанию 5
            Время ожидания в секундах.
        return_elem : bool, по умолчанию False
            Если True, возвращает найденный элемент.
        """
        start_time = time.time()
        element_locator = self.get_locator(locator_type, locator_value)
        try:
            # Первая попытка через Selenium
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(element_locator))
            element = self.get_element(locator_type, locator_value) if return_elem else True
            message = (
                f'Элемент с локатором: "{locator_type}" \n'
                f'И значением: "{locator_value}" \n'
                f'стал видимым через Selenium! \n'
                f'Время ожидания: {time.time() - start_time:.2f} секунд. \n'
            )
            logger.info(message)
            allure.attach(
                name="Успешное ожидание видимости элемента через Selenium",
                body=message,
                attachment_type=allure.attachment_type.TEXT
            )
            return element
        except TimeoutException as selenium_error:
            message = (
                f'Элемент с локатором: "{locator_type}" \n'
                f'И значением: "{locator_value}" \n'
                f'НЕ ВИДИМ через Selenium! \n'
                f'Время ожидания: {time.time() - start_time:.2f} секунд. \n\n'
                f'Ошибка: {selenium_error}.\n'
            )
            logger.info(message)
            allure.attach(
                name="ОШИБКА ожидания видимости элемента через Selenium",
                body=message,
                attachment_type=allure.attachment_type.TEXT
            )

            pass

        try:
            # Попытка через JavaScript
            element = self.get_element(locator_type, locator_value)
            is_visible = self.driver.execute_script(
                "return (arguments[0].offsetParent !== null) && (arguments[0].clientWidth > 0) && (arguments[0].clientHeight > 0);",
                element
            )
            if is_visible:
                if return_elem:
                    return element
                message = (
                    f'Элемент с локатором: "{locator_type}" \n'
                    f'И значением: "{locator_value}" \n'
                    f'Стал видимым через JavaScript! \n\n'
                    f'Время ожидания: {time.time() - start_time:.2f} секунд. \n'
                )
                logger.info(message)
                allure.attach(
                    name="Успешное ожидание видимости элемента через JavaScript",
                    body=message,
                    attachment_type=allure.attachment_type.TEXT
                )
                return True
        except Exception as js_exception:
            error_message = (
                f'Ошибка ожидания видимости элемента через JavaScript: \n'
                f'С локатором: "{locator_type}" \n'
                f'И значением: "{locator_value}" \n'
                f'Время ожидания: {time.time() - start_time:.2f} секунд. \n'
                f'Ошибка: {js_exception}.\n'
            )
            logger.error(error_message)
            allure.attach(
                name="Ошибка ожидания видимости через JavaScript",
                body=error_message,
                attachment_type=allure.attachment_type.TEXT
            )

        # Если ни один из способов не сработал
        self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
        final_error_message = (
            f'Элемент с локатором: "{locator_type}" \n'
            f'И значением: "{locator_value}" \n'
            f'НЕ СТАЛ ВИДИМЫМ. \n'
            "ВСЕ ПРОВЕРКИ ВИДИМОСТИ ЭЛЕМЕНТА, ЗАВЕРШИЛИСЬ НЕУДАЧЕЙ. \n"
        )
        logger.error(final_error_message)
        allure.attach(
            name="Финальная ошибка видимости элемента!",
            body=final_error_message,
            attachment_type=allure.attachment_type.TEXT
        )
        self._attach_debug_info_on_error(element_locator, timeout)
        assert False, final_error_message

    @allure.step('Ожидание наличия текста в элементе с локатором: {locator_type} и значением: {locator_value}')
    def wait_for_element_to_have_text(
            self,
            locator_type: str,
            locator_value: str,
            expected_text: str,
            timeout: int = 5
    ) -> bool:
        """
            Ожидает появления текста в элементе и проверяет его соответствие ожидаемому.

            Params:
            ----------
            locator_type : str
                Тип локатора (например, XPath, CSS_SELECTOR).
            locator_value : str
                Значение локатора для поиска элемента.
            expected_text : str
                Ожидаемый текст в элементе.
            timeout : int, по умолчанию 5
                Время ожидания в секундах.
        """
        full_locator = self.get_locator(locator_type, locator_value)
        element_text = None
        start_time = time.time()

        try:
            WebDriverWait(self.driver, timeout).until(
                EC.text_to_be_present_in_element_value(full_locator, expected_text)
            )
            element_text = self.driver.find_element(*full_locator).get_attribute('value')
            error_message = (
                f'Ожидаемый текст: "{expected_text}" \n'
                f'НЕ СООТВЕТСТВУЕТ \n'
                f'Фактическому тексту: {element_text} \n'
            )
            assert element_text == expected_text, error_message

            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.info(
                f'\nЭлемент с локатором: "{locator_type}" \n'
                f'содержит ожидаемый текст: "{expected_text}"'
            )
            allure.attach(
                name='Ожидание текста в элементе:',
                body=f'Ожидание текста "{expected_text}" в элементе: \n'
                     f'С локатором: "{locator_type}" и значением: "{locator_value}" \n'
                     f'Найденный текст: "{element_text}" \n'
                     f'Время ожидания: {elapsed_time:.2f} секунд',
                attachment_type=allure.attachment_type.TEXT)
            return True
        except AssertionError:
            end_time = time.time()
            elapsed_time = end_time - start_time
            error_message = (
                f'Ожидаемый текст: "{expected_text}", \n'
                f'Не соответствует фактическому тексту: "{element_text}" \n'
            )
            logger.error(error_message)
            allure.attach(
                name='Assertion Error',
                body=f'{error_message}\n '
                     f'Время ожидания: {elapsed_time:.2f} секунд \n',
                attachment_type=allure.attachment_type.TEXT
            )
            self._attach_debug_info_on_error(full_locator, timeout)
            assert False, error_message
        except TimeoutException:
            end_time = time.time()
            elapsed_time = end_time - start_time
            error_message = (
                f'Таймаут ожидания текста: "{expected_text}" \n'
                f"В элементе: \n"
                f'С локатором: "{locator_type}" \n'
                f'и значением: "{locator_value}" \n'
                f'Время ожидания: {elapsed_time:.2f} секунд \n'
            )
            logger.error(error_message)
            allure.attach(
                name='Timeout Exception',
                body=error_message,
                attachment_type=allure.attachment_type.TEXT
            )
            self._attach_debug_info_on_error(full_locator, timeout)
            assert False, error_message
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            error_message = (
                f'Ошибка ожидания текста: "{expected_text}" \n'
                f'в элементе: \n'
                f'С локатором: "{locator_type}" \n'
                f'и значением: "{locator_value}" \n'
                f'Тип ошибки: {type(e).__name__} \n'
                f'Время ожидания: {elapsed_time:.2f} секунд \n'
                f'Сообщение: {str(e)} \n'
            )
            logger.error(f'{error_message}.\n Ошибка: {e}')
            allure.attach(
                name=f'Exception: {type(e).__name__}',
                body=f'{error_message} \n'
                     f'Полное исключение: {repr(e)} \n',
                attachment_type=allure.attachment_type.TEXT
            )
            self._attach_debug_info_on_error(full_locator, timeout)
            self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
            assert False, error_message

    @allure.step("Ожидание начала загрузки файла")
    def wait_for_download_to_start(
            self,
            download_dir: str,
            file_name: str,
            timeout: int = 10
    ) -> bool:
        """
        Ждет начала скачивания файла, проверяя наличие файла в директории загрузок.

        :param download_dir: Директория, куда сохраняются скачанные файлы.
        :param file_name: Ожидаемое имя файла.
        :param timeout: Максимальное время ожидания в секундах.
        :return: True, если скачивание началось, иначе False.
        """
        end_time = time.time() + timeout
        logger.info(
            f'Ожидание появления файла: "{file_name}" \n'
            f'в директории: "{download_dir}" в течение {timeout} секунд.')

        while time.time() < end_time:
            if not os.path.exists(download_dir):
                error_message = f'Директория "{download_dir}" не существует.'
                logger.error(error_message)
                allure.attach(
                    name="Ошибка директории",
                    body=error_message,
                    attachment_type=allure.attachment_type.TEXT
                )
                return False

            files = os.listdir(download_dir)
            logger.info(f'Файлы в директории загрузок: "{files}" ')
            for file in files:
                if file_name in file:
                    logger.info(f'Файл: "{file_name}" найден в директории загрузок.')
                    return True
            time.sleep(1)

        logger.error(
            f'Файл: "{file_name}" НЕ НАЙДЕН \n'
            f'в директории загрузок в течение отведенного времени. \n'
        )
        return False
