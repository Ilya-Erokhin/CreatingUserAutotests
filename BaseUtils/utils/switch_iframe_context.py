import allure
from selenium.common.exceptions import NoSuchFrameException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Type
from BaseUtils.utils.logger import logger

# Карта типов локаторов для упрощения доступа по строковому ключу
locator_map = {
    "id": By.ID,
    "name": By.NAME,
    "class_name": By.CLASS_NAME,
    "link_text": By.LINK_TEXT,
    "xpath": By.XPATH,
    "css": By.CSS_SELECTOR
}


class SwitchIframeContext:
    def __init__(
            self,
            driver: WebDriver,
            locator_type: str,
            locator_value: str
    ) -> None:
        if locator_type not in locator_map:
            raise ValueError(f'Неверный тип локатора: "{locator_type}"')
        self.driver = driver
        self.locator_type = locator_type
        self.locator_value = locator_value
        self.locator = locator_map[locator_type]
        self.found_iframe_locator = None

    def __enter__(self) -> 'SwitchIframeContext':
        logger.info(
            f'Начало поиска элемента с локатором: "{self.locator_type}" \n'
            f'и значением: "{self.locator_value}" в iframe'
        )
        self.found_iframe_locator = self._find_element_in_iframes(
            driver=self.driver,
            locator=self.locator,
            locator_value=self.locator_value,
            iframe_locator='//*[@id="mainDocument"]'
        )
        if not self.found_iframe_locator:
            screenshot = self.driver.get_screenshot_as_png()
            with allure.step("Скриншот во время ошибки"):
                allure.attach(
                    name="Screenshot",
                    body=screenshot,
                    attachment_type=allure.attachment_type.PNG
                )
            error = (
                f"\n Ошибка при поиске элемента внутри <iframe> на странице. \n"
                f"ВОЗМОЖНАЯ ПРИЧИНА: НЕВЕРНО УКАЗАННЫЙ <iframe> \n"
                f"Обратитесь к автотестеру! \n"
                f"Элемент: \n"
                f'C локатором: "{self.locator_type}" \n'
                f'B значением: "{self.locator_value}" \n'
                f"НЕ НАЙДЕН НИ В ОДНОМ <iframe>.\n"
            )
            logger.error(error)
            raise AssertionError(error)
        logger.info(
            f'Элемент с локатором: "{self.locator_type}" \n'
            f'и значением: "{self.locator_value}" \n'
            f'НАЙДЕН'
        )
        return self

    def __exit__(
            self,
            exc_type: Type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: Type
    ) -> None:
        self.driver.switch_to.default_content()
        logger.info("\n\n Переключение в обычный режим после работы с <iframe>.\n\n")

    def _find_element_in_iframes(
            self,
            driver: WebDriver,
            locator: By,
            locator_value: str,
            iframe_locator: str
    ) -> str | None:
        """
        Рекурсивный поиск элемента в iframes.

        :param driver: WebDriver для управления браузером.
        :param locator: Тип локатора.
        :param locator_value: Значение локатора.
        :param iframe_locator: Локатор текущего iframe для отчетности.
        :return: Локатор iframe, если элемент найден, иначе None.
        """
        try:
            # Поиск элемента в текущем iframe
            WebDriverWait(driver, 4).until(
                EC.presence_of_element_located((self.locator, self.locator_value))
            )
            logger.info(f"Элемент НАЙДЕН в <iframe> с локатором: {iframe_locator}")
            return iframe_locator
        except TimeoutException:
            pass

        # Поиск в каждом вложенном iframe
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        for index, iframe in enumerate(iframes):
            try:
                logger.info(f'\n\nПереключение на <iframe> {index + 1} - с локатором: {locator_value}\n\n')
                driver.switch_to.frame(iframe)
                new_iframe_locator = f"{iframe_locator}//iframe[{index + 1}]"
                result = self._find_element_in_iframes(driver, locator, locator_value, new_iframe_locator)
                if result:
                    return result
                driver.switch_to.default_content()
            except (NoSuchFrameException, StaleElementReferenceException):
                screenshot = self.driver.get_screenshot_as_png()
                with allure.step("Скриншот во время ошибки"):
                    allure.attach(
                        name="Screenshot",
                        body=screenshot,
                        attachment_type=allure.attachment_type.PNG
                    )
                logger.warning(f"Не удалось переключиться на <iframe> с src: {iframe.get_attribute('src')}")
                driver.switch_to.default_content()

        return None
