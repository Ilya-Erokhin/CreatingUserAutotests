from datetime import datetime

import allure


@allure.feature('Автотесты на: Поиск пользователя, Проверку данных и Удаление пользователя.')
@allure.title('Автотесты на: Поиск пользователя, Проверку данных и Удаление пользователя.')
@allure.suite('Автотесты на: Поиск пользователя, Проверку данных и Удаление пользователя.')
class TestCreatingNewUser:

    @allure.title('Полный тестовый сценарий: Поиск пользователя, Проверка данных, Удаление')
    def test_create_and_verify_book(self, creating_new_user_page):
        current_date = datetime.now()
        formatted_date = current_date.strftime('%d.%m.%Y')
        creating_new_user_page.execute_full_user_creation_test(
            text_params_for_creating_user={
                'имя': 'Илья',
                'email': 'illiaero@gmail.com',
                'пароль': 'qwerty00110100',
                'дата': formatted_date,
                'начал_работать': formatted_date,
                'увлечение': 'Программирвоание',
                'имя1': 'Илья2',
                'фамилия1': 'Ерохин',
                'отчество1': 'Александрович',
                'кошечка': 'кошечка',
                'собачка': 'собачка',
                'попугайчик': 'попугайчик',
                'морская_свинка': 'морская_свинка',
                'хомячок': 'хомячок',
                'белочка': 'белочка',
                'телефон': '8912134132',
                'адрес': 'Санкт-Петербург',
                'ИНН': '0000000'
            },
            gender="Мужской",
        )
