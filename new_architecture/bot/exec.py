import os  # Библиотека для открытия файла .env

import telebot  # Сам бот
from dotenv import load_dotenv  # Библиотека для работы с .env
from loguru import logger  # loguru - пока самая удобная библиотека для логирования
from telebot import types, ExceptionHandler  # Импортируем типы данных библиотеки telebot

class TracebackHandler(ExceptionHandler):
    def handle(self, exception):
        logger.error(exception)


load_dotenv()  # Подключаем .env
bot = telebot.TeleBot(os.getenv("TOKEN"), exception_handler=TracebackHandler)  # Создаём объект бота
bot.enable_saving_states()

def run():
    bot.infinity_polling()