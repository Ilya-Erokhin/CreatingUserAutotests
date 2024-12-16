import allure
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Type, Optional
from BaseUtils.utils.logger import logger


class SwitchWindowContext:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.main_window_handle = self.driver.current_window_handle
        self.new_window_handle = None

    def __enter__(self) -> 'SwitchWindowContext':
        self.new_window_handle = self._find_new_window_handle()
        if not self.new_window_handle:
            self._take_screenshot()
            raise AssertionError("Новое окно НЕ НАЙДЕНО.")
        self.driver.switch_to.window(self.new_window_handle)
        return self

    def __exit__(self, exc_type: Type[BaseException], exc_val: BaseException, exc_tb: Type) -> None:
        if self.new_window_handle:
            try:
                if self.new_window_handle in self.driver.window_handles:
                    self.driver.close()  # Закрыть новое окно
                else:
                    logger.warning("Целевое окно уже закрыто.")
            except NoSuchWindowException:
                logger.warning("Целевое окно уже закрыто.")
        self.driver.switch_to.window(self.main_window_handle)
        logger.info("Выход из контекста окна, переключение в основное окно.")

    def _find_new_window_handle(self) -> Optional[str]:
        """
        Поиск хэндла нового окна.

        :return: Хэндл нового окна, если найден, иначе None.
        """
        try:
            all_window_handles = self.driver.window_handles
            for handle in all_window_handles:
                if handle != self.main_window_handle:
                    logger.info(f"Новое окно НАЙДЕНО с хэндлом: {handle}")
                    return handle
        except NoSuchWindowException:
            logger.warning("Не удалось найти новое окно.")
        return None

    def _take_screenshot(self):
        screenshot = self.driver.get_screenshot_as_png()
        with allure.step("Скриншот во время ошибки"):
            allure.attach(
                name="Screenshot",
                body=screenshot,
                attachment_type=allure.attachment_type.PNG
            )
