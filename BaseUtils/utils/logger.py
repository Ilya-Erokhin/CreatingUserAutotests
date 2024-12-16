from loguru import logger as loguru_logger
import sys


def setup_logger():
    """
    Настройка логера с использованием loguru.

    Returns:
        loguru.Logger: Объект логера.
    """
    # Очищаем любые стандартные обработчики
    loguru_logger.remove()

    # Настраиваем вывод в консоль с поддержкой цвета
    loguru_logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> \n"
               "| <level>{level}</level> | \n"
               "<cyan>{message}</cyan> \n"
               "================================================================================",
        level="INFO",
        colorize=True
    )

    return loguru_logger


# Настраиваем логгер с использованием loguru
logger = setup_logger()
