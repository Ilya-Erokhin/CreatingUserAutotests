import openpyxl
import os
from typing import List, Dict


class ExcelReader:
    def __init__(
            self,
            project_dir: str,
            file_name: str,
            column_names: Dict[str, int] | None = None
    ):
        """
        Инициализация класса для чтения данных из Excel.

        :param project_dir: Путь к корневой директории проекта.
        :param file_name: Имя файла Excel.
        :param column_names: Словарь, где ключи - имена столбцов, значения - номера столбцов (0-based).
                            Если не передан, заголовки будут взяты из первой строки Excel.
        """
        self.file_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '..',  # Вверх на один уровень
                '..',  # Вверх еще на один уровень
                project_dir,  # Папка проекта
                'credentials',  # Папка credentials
                file_name  # Имя файла Excel
            )
        )
        self.workbook = openpyxl.load_workbook(self.file_path)
        self.column_names: Dict[str, int] | None = column_names

    def get_data(
            self,
            sheet_name: str | None = None
    ) -> List[Dict[str, str | list[str]]]:
        """
        Чтение данных из указанного листа Excel и автоматическое преобразование
        ячеек с разделителем ';' в списки, если это необходимо.

        :param sheet_name: Имя листа в Excel.
        :return: Список словарей с данными.
        """
        sheet = self.workbook[sheet_name] if sheet_name else self.workbook.worksheets[0]
        data = []

        headers = None  # Инициализируем переменную headers как None

        # Если column_names не передан, используем заголовки из первой строки
        if self.column_names is None:
            headers = [cell.value for cell in sheet[1]]

        # Пропускаем первую строку (заголовки)
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if all(cell is None for cell in row):
                continue  # Пропускаем пустую строку

            row_data = {}

            if self.column_names:
                # Используем переданный column_names
                for col_name, col_index in self.column_names.items():
                    cell_value = row[col_index]
                    row_data[col_name] = self._process_cell_value(cell_value)
            else:
                # Используем заголовки из первой строки
                for col_index, cell_value in enumerate(row):
                    header = headers[col_index]
                    row_data[header] = self._process_cell_value(cell_value)

            data.append(row_data)

        return data

    @staticmethod
    def _process_cell_value(cell_value: str) -> int | str | None:
        """
        Обрабатывает значение ячейки: преобразует строки с разделителем ';' в списки,
        строки, начинающиеся с 'http' или 'https', также оборачиваются в список,
        а числа с плавающей запятой, являющиеся целыми, преобразуются в int.
        """
        if cell_value is None:
            return None
        elif isinstance(cell_value, str):
            return (
                cell_value.split(';') if ';' in cell_value else
                [cell_value] if cell_value.startswith(("http", "https")) else
                cell_value
            )
        elif isinstance(cell_value, float) and cell_value.is_integer():
            return int(cell_value)
        else:
            return str(cell_value)
