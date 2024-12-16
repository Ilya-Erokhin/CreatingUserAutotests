import os
import sys
import time

import allure

# Получаем абсолютный путь к корневой директории проекта
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from BaseUtils.configurations.config_reader import read_configuration
from BaseUtils.pages.base_page import BasePage
from BaseUtils.pages.login_page import LoginPage
from selenium.webdriver.remote.webdriver import WebDriver
from BaseUtils.utils.file_upload_page import FileUploadPage


class CreatingUser(BasePage):
    """
    Класс для работы со страницей "Пользователя".
    """

    def __init__(self, driver: WebDriver) -> None:
        """
        Инициализация страницы проверки карточки развития.
        :param driver: WebDriver - объект веб-драйвера для взаимодействия с браузером.
        """
        super().__init__(driver)
        self.login_page = LoginPage(driver=driver)
        self.file_upload_page = FileUploadPage(driver=driver, project_dir="Task_UserAuto")

    @allure.step('Открытие страницы "Пользователи"')
    def open_ku_settings_page(self) -> None:
        """
        Открывает страницу Пользователя.
        """
        self.navigate_to_url()

    @allure.step('Клик на кнопку "Добавить нового пользователя"')
    def click_add_user_button(self):
        """
        Клик на кнопку "Добавить нового пользователя"
        :return:
        """
        self.click_on_element(
            locator_type="xpath",
            locator_value="//a[text()='Добавить пользователя']"
        )

    @allure.step('Ввод параметров в текстовые поля для создания пользователя')
    def type_params_into_fields(
            self,
            text_params_for_creating_user: dict[str]
    ) -> dict[str]:
        """
        Метод для ввода параметров в текстовые поля для создания пользователя.
        """
        text_params_locators: dict[str] = {
            'имя': '//td[@data-field="name"]/*',
            'email': '//td[@data-field="email"]/*',
            'пароль': '//td[@data-field="password"]/*',
            'дата': '//input[@type="date"]',
            'начал_работать': '//input[@name="noibiz_date_start"]',
            'увлечение': '//td[@data-field="hobby"]/*',
            'имя1': '//td[@data-field="name1"]/*',
            'фамилия1': '//td[@data-field="surname1"]/*',
            'отчество1': '//td[@data-field="fathername1"]/*',
            'кошечка': '//td[@data-field="cat"]/*',
            'собачка': '//td[@data-field="dog"]/*',
            'попугайчик': '//td[@data-field="parrot"]/*',
            'морская_свинка': '//td[@data-field="cavy"]/*',
            'хомячок': '//td[@data-field="hamster"]/*',
            'белочка': '//td[@data-field="squirrel"]/*',
            'телефон': '//td[@data-field="phone"]/*',
            'адрес': '//td[@data-field="adres"]/*',
            'ИНН': '//td[@data-field="inn"]/*'
        }

        # Вводим параметры в каждое поле
        for field, locator in text_params_locators.items():
            self.type_into_element(
                locator_type="xpath",
                locator_value=locator,
                text_to_enter=text_params_for_creating_user.get(field)  # Вытягиваем значение по ключу
            )

        # Получаем значения для `email`, `имя`, и `дата` из text_params_for_creating_user
        email_full_name_author_data: dict[str] = {
            'email': text_params_for_creating_user.get('email'),
            'имя': text_params_for_creating_user.get('имя'),
            'дата': text_params_for_creating_user.get('дата'),
            'пароль': text_params_for_creating_user.get('пароль'),
        }

        return email_full_name_author_data

    @allure.step('Выбор изображения аватара пользователя')
    def choose_avatar_img(self) -> None:
        """
        Выбор аватара пользователя локально с ПК
        :return: None
        """
        self.file_upload_page.drop_file_into_field(
            locator_type="xpath",
            locator_value='//input[@name="noibiz_avatar"]',
            file_name="kitty.jpg"
        )

    @allure.step('Выбор пола: {gender} из выпадающего списка')
    def choose_gender(self, gender: str) -> None:
        """
        Выбор пола из выпадающего списка
        :return: None
        """
        self.select_from_dropdown(
            locator_type="xpath",
            locator_value='//select[@name="noibiz_gender"]',
            option_text=gender
        )

    @allure.step('Клик на кнопку "Добавить пользователя" после его создания')
    def click_add_user_after_creating(self) -> None:
        """
        Клик на кнопку "Добавить пользователя" после его создания
        :return: None
        """
        self.click_on_element(
            locator_type="xpath",
            locator_value='//input[@value="Добавить пользователя"]'
        )

    @allure.step('Поиск пользователя в списке и переход к его карточке')
    def find_user_and_open_profile(self, username: str) -> None:
        """
        Находит пользователя по имени в списке и нажимает на кнопку "Посмотреть".

        :param username: str - имя пользователя для поиска.
        :return: None
        """
        self.type_into_element(
            locator_type="xpath",
            locator_value='//input[@placeholder="Введите email или имя"]',
            text_to_enter=username
        )

    @allure.step('Клик на кнопку "Найти" для поиска пользователя')
    def click_search_user_button(self) -> None:
        """
        Клик на кнопку "Найти" для поиска пользователя
        :return: None
        """
        self.click_on_element(
            locator_type="xpath",
            locator_value="//button[text()='Найти']"
        )

    @allure.step('Сравнение данных профиля с исходными')
    def compare_profile_data(
            self,
            expected_data: list[str]
    ) -> bool:
        """
        Сравнивает данные, введенные при создании пользователя, с отображаемыми в профиле.

        :param expected_data: dict - исходные данные пользователя.
        :return: bool - True, если данные совпадают, иначе False.
        """
        xpath_values = [
            "//tbody[@class='ajax_load_row']/tr[1]/td[1]",  # email
            "//tbody[@class='ajax_load_row']/tr[1]/td[2]",  # ФИО
            "//tbody[@class='ajax_load_row']/tr[1]/td[3]",  # Автор
            "//tbody[@class='ajax_load_row']/tr[1]/td[4]",  # Дата создания
        ]

        for xpath_value, expected_value in zip(xpath_values, expected_data):
            with allure.step(f'Проверка значения поля'):
                self.assert_text_in_element(
                    locator_type="xpath",
                    locator_value=xpath_value,
                    at_least_text=expected_value
                )

    @allure.step('Выход из учетной записи пользователя Админ')
    def logout(self) -> None:
        """
        Выход из учетной записи пользователя Админ
        :return: None
        """
        self.click_on_element(
            locator_type="css",
            locator_value="#fat-menu"
        )
        self.click_on_element(
            locator_type="xpath",
            locator_value="//a[text()='Выход']"
        )

    @allure.step('Логин под новым пользователем')
    def login_new_user(
            self,
            login: str,
            password: str
    ) -> None:
        self.login_page.login(
            username=login,
            password=password
        )

    @allure.step('Удаление пользователя из системы')
    def delete_user(self, username: str) -> None:
        """
        Удаляет пользователя из системы через интерфейс менеджера.

        :param username: str - имя пользователя для удаления.
        :return: None
        """
        self.find_user_and_open_profile(username=username)
        self.click_on_element(
            locator_type="xpath",
            locator_value="//a[text()='Удалить']"
        )

    def execute_full_user_creation_test(
        self,
        text_params_for_creating_user: dict[str, str],
        gender: str,
    ) -> None:
        """
        Выполняет полный сценарий: поиск пользователя, проверка данных, удаление.

        :param text_params_for_creating_user: dict[str, str] - параметры для ввода в текстовые поля.
        :param gender: str - пол пользователя.
        :return: None
        """
        # Открываем страницу пользователей
        self.open_ku_settings_page()

        # Нажимаем на кнопку добавления нового пользователя
        self.click_add_user_button()

        # Вводим параметры пользователя
        params = self.type_params_into_fields(
            text_params_for_creating_user=text_params_for_creating_user
        )
        email = params['email']
        name = params['имя']
        date = params['дата']
        password = params['пароль']
        author: str = read_configuration(
            category="credentials",
            key="login",
        )

        # Выбираем изображение аватара пользователя
        self.choose_avatar_img()

        # Выбираем пол пользователя
        self.choose_gender(gender=gender)

        # Добавляем созданного пользователя
        self.click_add_user_after_creating()

        # Клик на кнопку "Найти"
        self.click_search_user_button()

        # Проверяем данные профиля
        self.compare_profile_data(expected_data=[email, name, author, date])

        # Выходим из учетной записи
        self.logout()

        email_amd = read_configuration(
            category="credentials",
            key="login",
        )
        password_adm = read_configuration(
            category="credentials",
            key="password",
        )
        # Логинимся под новым пользователем
        self.login_new_user(login=email_amd, password=password_adm)

        # Удаляем пользователя
        self.delete_user(username=name)

