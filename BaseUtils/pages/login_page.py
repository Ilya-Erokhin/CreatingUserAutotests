import allure
from BaseUtils.pages.base_page import BasePage
from selenium.webdriver.remote.webdriver import WebDriver


class LoginPage(BasePage):
    """
    Класс LoginPage предоставляет методы для взаимодействия с формой авторизации на странице.
    Наследуется от BasePage.
    """

    def __init__(self, driver: WebDriver):
        """
        Инициализирует объект LoginPage.

        Args:
            driver (WebDriver): Экземпляр WebDriver для взаимодействия с браузером.
        """
        super().__init__(driver)

    @allure.step("Открытие страницы входа")
    def open_login_page(self) -> None:
        """
        Открывает страницу входа.

        Вызывает метод navigate_to_base_url() унаследованного класса BasePage
        для навигации на базовый URL приложения.
        """
        self.navigate_to_url()

    @allure.step('Клик на кнопку "Войти"')
    def click_enter_button(self):
        """
        Клик на кнопку "Войти"
        """
        self.click_on_element(
            locator_type="xpath",
            locator_value="//span[text()='Войти']"
        )

    @allure.step("Ввод логина: {login}")
    def enter_login_username(self, login: str) -> None:
        """
        Вводит логин на странице авторизации.

        Args:
            login (str): Логин пользователя.
        """
        self.type_into_element(
            locator_type="xpath",
            locator_value='//input[@name="login"]',
            text_to_enter=login
        )

    @allure.step("Ввод пароля: {password}")
    def enter_password(self, password: str) -> None:
        """
        Вводит пароль на странице авторизации.

        Args:
            password (str): Пароль пользователя.
        """
        self.type_into_element(
            locator_type="xpath",
            locator_value='//input[@type="password"]',
            text_to_enter=password
        )

    @allure.step("Нажатие кнопки 'Авторизоваться'")
    def click_login_button(self) -> None:
        """
        Нажимает кнопку "Авторизоваться" на странице авторизации.
        """
        self.click_on_element(
            locator_type="xpath",
            locator_value='//input[@value="Авторизоваться"]'
        )

    @allure.step("Выполнение авторизации с логином: {username} и паролем: {password}")
    def login(self, username: str, password: str) -> None:
        """
        Выполняет авторизацию на странице.

        Args:
            username (str): Логин пользователя.
            password (str): Пароль пользователя.
        """
        self.open_login_page()
        self.click_enter_button()
        self.enter_login_username(login=username)
        self.enter_password(password=password)
        self.click_login_button()
