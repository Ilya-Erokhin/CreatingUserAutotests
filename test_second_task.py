import pytest
from pydantic import BaseModel


# Модель ответа метода
class AnalysisResult(BaseModel):
    min: int
    max: int
    avg: int
    sum: int
    even_cnt: int
    odd_cnt: int


def number_analysis(*args: int) -> AnalysisResult:
    """
    Анализирует последовательность чисел и возвращает модель с информацией:
    - min: минимальное число последовательности
    - max: максимальное число последовательности
    - avg: среднее значение всех элементов последовательности
    - sum: сумма всех элементов
    - even_cnt: количество четных чисел
    - odd_cnt: количество нечетных чисел

    :param args: Последовательность целых чисел
    :return: Модель типа AnalysisResult с результатами анализа
    :raises ValueError: если входящие данные содержат нецелые числа
    """
    if not all(isinstance(x, int) for x in args):
        raise ValueError("Все входящие данные должны быть целыми числами")

    total_count = len(args)
    total_sum = sum(args)
    min_value = min(args)
    max_value = max(args)
    even_count = sum(1 for x in args if x % 2 == 0)
    odd_count = total_count - even_count
    avg_value = total_sum // total_count  # Среднее целое значение!

    return AnalysisResult(
        min=min_value,
        max=max_value,
        avg=avg_value,
        sum=total_sum,
        even_cnt=even_count,
        odd_cnt=odd_count
    )


# Тесты
def test_number_analysis_positive() -> None:
    """
    Тест на позитивный случай.
    Проверяем корректность работы метода для допустимых входных данных.

    :return None
    """
    result = number_analysis(1, 2, 3, 4, 5)

    assert result.min == 1
    assert result.max == 5
    assert result.avg == 3
    assert result.sum == 15
    assert result.even_cnt == 2
    assert result.odd_cnt == 3


def test_number_analysis_negative() -> None:
    """
    Тест на негативный случай.
    Проверяем, что метод бросает исключение ValueError при некорректных входных данных.

    :return None
    """
    with pytest.raises(
            ValueError,
            match="Все входящие данные должны быть целыми числами"
    ):
        number_analysis(1, 2, 'three', 4)
