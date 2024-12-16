import mimetypes
import tempfile
import time
import urllib.parse
import allure
import requests
from requests import RequestException

from BaseUtils.pages.base_page import BasePage
from selenium.webdriver.remote.webdriver import WebDriver
import os

from BaseUtils.utils.logger import logger


class FileUploadPage(BasePage):
    """
    Класс для страницы с функционалом загрузки файлов.
    """

    def __init__(self, driver: WebDriver, project_dir: str) -> None:
        super().__init__(driver)
        self.project_dir = project_dir

    @allure.step('Загрузка файла: "{file_name}" в поле со локатором: {locator_type}={locator_value}')
    def drop_file_into_field(
            self,
            locator_type: str,
            locator_value: str,
            file_name: str
    ) -> None:
        """
        Загрузка файла на страницу через поле ввода файла.

        :param file_name: Имя файла в папке credentials.
        :param locator_type: Тип локатора (id, xpath, css, class_name)
        :param locator_value: Значение локатора
        """
        # Определение абсолютного пути к файлу
        file_path = os.path.abspath(os.path.join('..', self.project_dir, 'credentials', file_name))

        field_locator: tuple = (locator_type, locator_value)
        # Логирование начала операции
        logger.info(f"Попытка загрузки файла '{file_name}' в поле с локатором {field_locator}")
        logger.info(f"Определенный путь к файлу: {file_path}")

        try:
            # Поиск элемента для загрузки файла
            file_input = self.get_element(locator_type, locator_value)

            # Определение расширения файла
            _, file_extension = os.path.splitext(file_name)

            if file_extension == '.txt':
                # Чтение содержимого файла, если это текстовый файл
                with open(file_path, 'r', encoding='utf-8') as file:
                    file_content = file.read()
                # Отправка содержимого файла в поле ввода
                file_input.send_keys(file_content)
            else:
                # Отправка пути к файлу в поле ввода для всех остальных типов файлов
                file_input.send_keys(file_path)

            # Определение типа файла для прикрепления к Allure
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                if mime_type.startswith('image/png'):
                    attachment_type = allure.attachment_type.PNG
                elif mime_type.startswith('image/jpeg'):
                    attachment_type = allure.attachment_type.JPG
                elif mime_type == 'application/pdf':
                    attachment_type = allure.attachment_type.PDF
                elif mime_type.startswith('text/txt'):
                    attachment_type = allure.attachment_type.TEXT
                else:
                    attachment_type = allure.attachment_type.TEXT
            else:
                attachment_type = allure.attachment_type.TEXT

            # Прикрепление информации о загруженном файле в Allure
            with open(file_path, 'rb') as file:
                allure.attach(file.read(), name="Загруженный файл", attachment_type=attachment_type)

            logger.info(f"Файл '{file_name}' успешно загружен в поле с локатором {field_locator}")
            time.sleep(1)

        except FileNotFoundError:
            logger.error(f"Файл {file_path} не найден.")
            allure.attach(f"Файл {file_path} не найден.", name="FileNotFoundError",
                          attachment_type=allure.attachment_type.TEXT)
            raise FileNotFoundError(f"Файл {file_path} не найден.")
        except IOError as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")
            allure.attach(f"Ошибка чтения файла {file_path}: {e}", name="IOError",
                          attachment_type=allure.attachment_type.TEXT)
            raise IOError(f"Ошибка чтения файла {file_path}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла: {e}")
            allure.attach(f"Ошибка при загрузке файла: {e}", name="Exception",
                          attachment_type=allure.attachment_type.TEXT)
            raise RuntimeError(f"Ошибка при загрузке файла: {e}")

    @allure.step('Загрузка файла по ссылке {link} в поле {locator_type}={locator_value}')
    def load_file_via_link(
            self,
            locator_type: str,
            locator_value: str,
            link: str
    ) -> None:
        temp_file_name = None  # Инициализация переменной для использования в блоке finally
        try:
            # Проверка на корректность URL
            parsed_url = urllib.parse.urlparse(link)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ValueError(f"Некорректный URL: {link}")

            logger.info(f"Проверка ссылки: {link}")

            logger.info(f"Скачивание файла по ссылке: {link}")

            # Скачиваем файл по ссылке
            response = requests.get(link)
            response.raise_for_status()  # Проверка на успешность запроса

            # Определяем тип файла и расширение
            content_type = response.headers.get('Content-Type')
            extension = mimetypes.guess_extension(content_type) or ''

            # Создаем временный файл с динамическим расширением
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
                tmp_file.write(response.content)
                temp_file_name = tmp_file.name  # Получаем имя временного файла

            logger.info(f"Файл успешно скачан и сохранен как временный файл: {temp_file_name}")

            # Используем метод drop_file_into_field для загрузки файла
            self.drop_file_into_field(locator_type, locator_value, temp_file_name)

        except ValueError as ve:
            logger.error(f"Ошибка при проверке URL: {ve}")
            allure.attach(f"Ошибка при проверке URL: {ve}", name="ValueError",
                          attachment_type=allure.attachment_type.TEXT)
            self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
            assert False, f"Ошибка при проверке URL: {ve}"

        except RequestException as e:
            logger.error(f"Ошибка при скачивании файла: {e}")
            allure.attach(f"Ошибка при скачивании файла: {e}", name="RequestException",
                          attachment_type=allure.attachment_type.TEXT)
            self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
            assert False, f"Ошибка при скачивании файла: {e}"

        except Exception as e:
            logger.error(f"Ошибка при загрузке файла: {e}")
            allure.attach(f"Ошибка при загрузке файла: {e}", name="Exception",
                          attachment_type=allure.attachment_type.TEXT)
            self.take_screenshot_when_error_and_scroll(locator_type, locator_value)
            assert False, f"Ошибка при загрузке файла: {e}"

        finally:
            # Проверяем, что файл существует, прежде чем удалять его
            if temp_file_name and os.path.exists(temp_file_name):
                try:
                    os.remove(temp_file_name)
                except PermissionError:
                    logger.error(
                        f"Не удалось удалить временный файл: {temp_file_name}, файл используется другим процессом.")
