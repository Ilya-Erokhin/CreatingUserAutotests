import allure

from BaseUtils.pages.base_page import BasePage
from selenium.webdriver.remote.webdriver import WebDriver
from BaseUtils.configurations.config_reader import read_configuration


class SetUncompletedPrograms(BasePage):

    def __init__(self, driver: WebDriver):
        super().__init__(driver)
        self.corp_university_settings_endpoint = read_configuration(
            category="basic info",
            key="corp_university_settings_endpoint",
        )

    @allure.step("Открытие страницы 'Настройки Корпоративного университета'")
    def open_corp_university_settings_page(self) -> None:
        self.navigate_to_url(
            endpoint=self.corp_university_settings_endpoint
        )

    @allure.step('Закрытие окна "Битрикс24 - Единая авторизация"')
    def close_alert_window(self) -> bool:
        if self.wait_utils.wait_for_element_to_be_visible(
            locator_type="xpath",
            locator_value="//span[text()='Битрикс24 - Единая авторизация']"
        ):
            self.click_on_element(
                locator_type="xpath",
                locator_value='//input[@value="Закрыть"]'
            )
            return True
        else:
            allure.attach(
                name="Пропуск шага",
                body="Пропуск шага закрытия окна 'Битрикс24 - Единая авторизация'"
            )
            pass

    @allure.step('Установка количества дней')
    def set_num_of_uncompleted_programs(self, num_of_uncompleted_programs: str) -> bool:
        count_of_days_locator = "//span[text()='Количество не завершенных программ, одновременно находящихся у сотрудника:']/following-sibling::input[@type='text']"
        self.type_into_element(
            locator_type="xpath",
            locator_value=count_of_days_locator,
            text_to_enter=num_of_uncompleted_programs
        )

    @allure.step('Клик на кнопку "Сохранить"')
    def click_on_save_button(self):
        self.click_on_element(
            locator_type="xpath",
            locator_value='//input[@value="Сохранить"]'
        )

    @allure.step('Установка количества не завершенных программ, одновременно находящихся у сотрудника')
    def all_steps_to_set_days(self, num_of_uncompleted_programs: str):
        """
        Общий метод для установки количества не завершенных программ, одновременно находящихся у сотрудника
        """
        pass
        self.open_corp_university_settings_page()
        self.close_alert_window()
        self.set_num_of_uncompleted_programs(num_of_uncompleted_programs)
        self.click_on_save_button()
