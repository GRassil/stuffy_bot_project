import os  # Библиотека для открытия файла .env

import telebot  # Сам бот
from dotenv import load_dotenv  # Библиотека для работы с .env
from loguru import logger  # loguru - пока самая удобная библиотека для логирования
from telebot import types  # Импортируем типы данных библиотеки telebot

from making_excel_with_statistic import make_excel  # Создаёт эксель файл со статистикой учеников
from models import *  # ORM

load_dotenv()  # Подключаем .env
bot = telebot.TeleBot(os.getenv("TOKEN"), parse_mode='HTML')  # Создаём объект бота
payments = os.getenv("PAYMENTS_TOKEN")


def is_admin(message: types.Message) -> bool:
    """Проверка пользователя на админа"""

    # Сравнивает telegram_id чата с telegram_id админов в файле .env
    b = str(message.chat.id) in os.getenv("ADMINS").split(sep=",")

    # Вывод информации о результатах проверки: True - админ, False - нет
    logger.info(f"is admin checking: {b}")

    # Возвращет bool объект - результат проверки на админа
    return b


def on_starting():
    """Уведомляет админов, что бот начал работу"""

    # Пишет в чат поддержки, что бот запущен
    bot.send_message(chat_id=os.getenv("HELP_CHAT"), text="БОТ ЗАПУЩЕН /start")

    # Вывод в лог
    logger.info(f"___СТАРТ___")


# функция для отправки сообщения и удаления предыдущего сообщения
def send_msg(message: types.Message,
             chat_id: int | str,
             text: str,
             reply_markup=None,
             how_many_message_to_del: int = 1,
             parse_mode="HTML"):
    try:
        for i in range(how_many_message_to_del):
            bot.delete_message(chat_id=chat_id,
                               message_id=message.message_id - i)
    except Exception as e:
        logger.error(e)
    finally:
        return bot.send_message(chat_id=chat_id,
                                text=text,
                                reply_markup=reply_markup,
                                parse_mode=parse_mode)


@bot.message_handler(commands=["start"])
def start(message: types.Message):
    """Стартовый обработчик (Обработчик при команде '/start')"""
    bot.clear_step_handler(message)
    try:
        # Создание клавиатуры
        kb = types.InlineKeyboardMarkup()

        # Попытка получить данные пользователя
        with conn:
            user = User.get_or_none(user_id=message.chat.id)

        # Если новый пользователь
        if not user:
            # Вывод инфы в лог
            logger.info(
                f'Написал новый пользователь {message.from_user.username}'
                f'{message.from_user.full_name} {message.chat.id}')

            # Создание кнопок и добавление в клавиатуру
            btn1 = types.InlineKeyboardButton(text="Подписаться", url="https://t.me/dushnilamath")  # url-кнопка
            btn2 = types.InlineKeyboardButton(text="Регистрация",
                                              callback_data="registration")  # переход на регистрацию
            kb.add(btn1, btn2)  # Добавление кнопок в клавиатуру

            # Отправка сообщения
            send_msg(
                message=message,
                how_many_message_to_del=1,
                chat_id=message.chat.id,
                text="""Привет, я тот самый бот душнила, помогу тебе сдать экзамен на максимум!
                \n Давай подпишемся на канал неДУШНАЯ математика и продолжим регистрацию""",
                reply_markup=kb)

        # Если админ
        elif is_admin(message):
            logger.info(f'Написал админ {message.from_user.full_name} {message.from_user.username}')  # Вывод инфы в лог
            teacher_menu(message)  # Переход в меню для учителя

        # Если юзер уже зарегистрирован
        else:
            # Вывод инфы в лог
            logger.info(f'Написал пользователь {message.from_user.full_name} {message.from_user.username}')
            # Переход в меню ученика
            student_menu(message)

    except Exception as e:
        logger.error(e)


# Изменение уровня подписки от наличия юзера в группе или на канале
@bot.chat_member_handler(func=lambda upd: upd)
def course_level(update: types.ChatMemberUpdated):
    logger.debug(
        f"{update.new_chat_member.user.username} ({update.new_chat_member.user.id}) "
        f"теперь {update.new_chat_member.status} {update.chat.title}")
    with conn:
        user = User.get_or_none(User.user_id == update.new_chat_member.user.id)
        try:
            # Если пользователь ещё не зарегистрирован в боте
            if user is None:
                pass
            # Если он теперь участник чата недушного курса
            elif update.chat.id == int(os.getenv("NO_STUFFY_COURSE")) and update.new_chat_member.status == "member":
                user.if_get_course = 2
            # Если пользователь теперь участник чата душного курса
            elif update.chat.id == int(os.getenv("STUFFY_COURSE")) and update.new_chat_member.status == "member":
                user.if_get_course = 1
            user.save(force_insert=True)
        except Exception as e:
            logger.error(e)
            user.if_get_course = 0
        user.save(force_insert=True)


@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback: types.CallbackQuery):
    """Обработчик callback-запросов от Inline-кнопок"""

    # Очистка контекста, чтобы бот не регистрировал новые сообщения от пользователя, когда они не нужны.
    bot.clear_step_handler_by_chat_id(chat_id=callback.message.chat.id)

    # Вывод текста callback-запроса в лог
    logger.info(f"{callback.from_user.username} {callback.from_user.full_name} вызвал {callback.data}")

    with conn:
        user = User.get_or_none(User.user_id == callback.message.chat.id)
        # Возвращает данные о пользователе или None, если записи нет
    if not user:  # Если записи нет -> регистрация
        send_msg(
            message=callback.message,
            chat_id=callback.message.chat.id,
            text="Ой, я тебя чуток забыл, айда познакомимся снова",
            how_many_message_to_del=2)
        start(callback.message)

    # Проверка по 1 части запроса
    match callback.data.split(",")[0]:

        # Меню для учителя
        case "teacher menu":
            teacher_menu(message=callback.message)

        # Меню для учителя
        case "update theory":
            theory_menu(message=callback.message)

        # Меню добавления упражнения
        case "new exercise":
            add_exercise(message=callback.message)

        # Меню добавления варианта
        case "new test":
            add_test(message=callback.message)

        # Меню проверки варианта
        case "check test":
            test_checking_menu(message=callback.message)

        # Сдать проверку пробника
        case "submit test checking":
            result_id = int(callback.data.split(",")[1])
            submit_test_check(message=callback.message,
                              result_id=result_id)

        # Меню добавления домашнего задания
        case "new homework":
            add_homework(message=callback.message)

        # Меню проверки ДЗ
        case "check homework":
            homework_checking_menu(message=callback.message)

        # Сдать проверку дз
        case "submit homework checking":
            result_id = int(callback.data.split(",")[1])
            submit_homework_check(message=callback.message,
                                  result_id=result_id)

        # Рассылка нового видео
        case "sender":
            sender(message=callback.message)

        # Меню статистики учеников
        case "students` statistic":
            students_statistic(message=callback.message)

        # Ответ от учителя
        case 'teacher answer':
            user_id = int(callback.data.split(",")[1])
            answer(message=callback.message,
                   answer_from="Препода",
                   user_id=user_id)

        # Ответ от техподдержки
        case "support answer":
            user_id = int(callback.data.split(",")[1])
            answer(message=callback.message,
                   answer_from="техподдержки",
                   user_id=user_id)

        # Регистрация
        case "registration":
            registration(message=callback.message)

        case "send_db":
            send_database(message=callback.message)

        # Меню
        case "student menu":
            student_menu(message=callback.message)

        # Профиль пользователя
        case "profile":
            profile(message=callback.message)

        # Меню заданий
        case "do exercises":
            exercise_menu(message=callback.message)

        # Перемещение по меню заданий
        case 'exercise to':
            num = int(callback.data.split(",")[1])  # Задание для решения
            page = int(callback.data.split(",")[2])  # Страница для перехода
            exercise_menu(message=callback.message, page=page, num=num)

        # Меню тестов
        case "do test":
            test_menu(message=callback.message,
                      page=1)

        # Перемещение по меню пробников
        case 'test to':
            page = int(callback.data.split(",")[1])  # Страница для перехода
            test_menu(message=callback.message,
                      page=page)

        # Сдать ответы пробника
        case "submit test answers":
            test_id = int(callback.data.split(",")[1])  # Тест для сдачи ответов
            submit_test_answers(message=callback.message,
                                test_id=test_id)

        # Вывод результатов пробника
        case "send test result":
            test_id = int(callback.data.split(",")[1])  # Тест для получения результатов
            send_test_results(message=callback.message,
                              test_id=test_id)

        # Меню дз
        case "do homework":
            homework_menu(message=callback.message,
                          page=1)

        # Перемещение по меню пробников
        case 'homework to':
            page = int(callback.data.split(",")[1])  # Страница для перехода
            homework_menu(message=callback.message,
                          page=page)

        # Сдать дз
        case "submit homework answers":
            hw_id = int(callback.data.split(",")[1])  # Дз для сдачи ответов
            submit_homework_answers(message=callback.message,
                                    hw_id=hw_id)

        # Результаты дз
        case "send homework result":
            hw_id = int(callback.data.split(",")[1])  # Дз для сдачи ответов
            send_homework_results(message=callback.message,
                                  hw_id=hw_id)

        case "course_shop":
            course_shop(callback.message)

        # Меню обратиться преподу
        case "chat with teacher":
            message_admin_menu(message=callback.message,
                               mode="teacher")

        # Меню "Обратиться в техподдержку"
        case "SOS":
            message_admin_menu(message=callback.message,
                               mode="support")
        # Меню с теорией
        case "theory":
            theory(message=callback.message)


"""Часть для учителя и админов"""


# Меню для учителя
def teacher_menu(message: types.Message):
    # Создание клавиатуры
    kb = types.InlineKeyboardMarkup(row_width=1)

    # Создание кнопок
    btn1 = types.InlineKeyboardButton("Добавить задания", callback_data="new exercise")
    btn2 = types.InlineKeyboardButton("Просмотреть задания", callback_data="check exercises")
    btn3 = types.InlineKeyboardButton("Добавить вариант", callback_data="new test")
    btn4 = types.InlineKeyboardButton("Проверить вариант", callback_data="check test")
    btn5 = types.InlineKeyboardButton("Добавить дз", callback_data="new homework")
    btn6 = types.InlineKeyboardButton("Проверить дз", callback_data="check homework")
    btn7 = types.InlineKeyboardButton("Статистика учеников", callback_data="students` statistic")
    btn8 = types.InlineKeyboardButton("Рассылка курсовикам", callback_data="sender")
    btn9 = types.InlineKeyboardButton("Просмотреть меню для учеников", callback_data="student menu")
    btn10 = types.InlineKeyboardButton("Добавить теорию", callback_data="update theory")
    btn11 = types.InlineKeyboardButton("Прислать базу данных", callback_data="send_db")

    # Добавление кнопок в клавиатуру
    kb.add(btn7)
    kb.row(btn1, btn2)
    kb.row(btn3, btn4)
    kb.row(btn5, btn6)
    kb.add(btn8, btn9, btn10, btn11)

    # Вывод меню
    try:
        send_msg(
            message=message,
            text="Что сделаем,Хозяин?",
            chat_id=message.chat.id,
            reply_markup=kb)
    except Exception as e:
        logger.error(e)


# Меню добавления теории
def theory_menu(message: types.Message):
    theory_file = Theory()

    # Получение типа теории
    def get_type(message: types.Message):
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="ГЕОМ или АЛГЕБРА")
        kb.add(types.KeyboardButton("ГЕОМ"))
        kb.add(types.KeyboardButton("АЛГЕБРА"))

        sent = send_msg(message=message,
                        chat_id=message.chat.id,
                        text="ГЕОМ или АЛГЕБРА?",
                        reply_markup=kb)
        bot.register_next_step_handler(sent, get_file)

    # Получение файла
    def get_file(message: types.Message):
        nonlocal theory_file
        theory_file.t_type = message.text
        sent = send_msg(message=message,
                        chat_id=message.chat.id,
                        text="Пришли файл",
                        reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(sent, finish)

    # Сохранение файла в базе данных
    def finish(message: types.Message):
        nonlocal theory_file
        theory_file.file_id = message.document.file_id
        with conn:
            old_file, created = Theory.get_or_create(t_type=theory_file.t_type,
                                                     defaults={"t_type": theory_file.t_type,
                                                               "file_id": theory_file.file_id})
            if not created:
                old_file = theory_file
                old_file.save()

            is_saved = bool(Theory.get_or_none(t_type=theory_file.t_type))
            logger.debug(f"Статус сохранения:{is_saved}")
        if is_saved:
            send_msg(message=message,
                     chat_id=message.chat.id,
                     text="Успех, нажми на /start чтобы перейти в меню",
                     how_many_message_to_del=2)
        else:
            theory_menu(message)

    # Запуск
    get_type(message=message)


# Добавление задачи в банк
def add_exercise(message: types.Message):
    exercise = Exercise()

    # Получение типа экзамена для задачи
    def add_exercise_type(message: types.Message):
        try:
            # Создание клавиатуры, добавление кнопок
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                           input_field_placeholder="ПРОФИЛЬ/БАЗА/ОГЭ")
            btn1 = types.KeyboardButton("ПРОФИЛЬ")
            btn2 = types.KeyboardButton("БАЗА")
            btn3 = types.KeyboardButton("ОГЭ")
            kb.add(btn1, btn2, btn3)

            # Бот запрашивает тип экзамена задачи и регистрирует следующее сообщение
            sent = send_msg(message=message,
                            how_many_message_to_del=2,
                            chat_id=message.chat.id,
                            text="Задача для какого экзамена?",
                            reply_markup=kb,
                            )
            bot.register_next_step_handler(sent, add_exercise_answer)
        except Exception as e:
            logger.error(e)

    # Получение ответа на задачу
    def add_exercise_answer(message: types.Message):
        nonlocal exercise

        # Запись ответа в объект класса задачи
        exercise.exam_type = message.text

        # Бот запрашивает ответ задачи и регистрирует следующее сообщение
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Какой ответ на задачу?",
                        reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(sent, add_exercise_number_in_test)

    # Получение номера задачи, которому эквивалентна добавляемая задача
    def add_exercise_number_in_test(message: types.Message):
        nonlocal exercise
        # Запись ответа в объект класса задачи
        exercise.right_answer = message.text
        # Бот запрашивает, какому номеру в тесте соответствует задача, и регистрирует следующее сообщение
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Какому номеру в тесте соответствует это задание")
        bot.register_next_step_handler(sent, add_exercise_ph)

    # Получение фотографии задания
    def add_exercise_ph(message: types.Message):
        nonlocal exercise
        # Запись ответа в объект класса задачи
        exercise.number_of_ex_in_test = message.text
        # Бот запрашивает фото задачи и регистрирует следующее сообщение
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Пришлите фотографию")
        bot.register_next_step_handler(sent, add_exercise_finish)

    # Сохранение данных в БД
    def add_exercise_finish(message: types.Message):
        nonlocal exercise
        try:
            # Запись ответа в объект класса задачи
            exercise.file_id = message.photo[-1].file_id
            # Сохранение объекта Задачи в БД
            with conn:
                exercise.save(force_insert=True)
            # Создание клавиатуры, добавление кнопок
            kb = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("В меню", callback_data="teacher menu")
            btn2 = types.InlineKeyboardButton(
                "Добавить задание", callback_data="new exercise"
            )
            kb.add(btn1, btn2)

            # Отправка сообщения об успешном сохранении данных
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=message.chat.id,
                     text=f"УСПЕШНО ДОБАВЛЕНО "
                          f"\nЭкзамен: {exercise.exam_type} "
                          f"\nНомер файла: {exercise.file_id} "
                          f"\nОтвет: {exercise.right_answer}",
                     reply_markup=kb)
        except Exception as e:
            logger.error(e)
            # В случае ошибки запрашивает фотографию заново

            # Создание клавиатуры, добавление кнопок
            kb = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("Отмена, в меню", callback_data="teacher menu")
            btn2 = types.InlineKeyboardButton(
                "Добавить всё заново", callback_data="new exercise"
            )
            kb.add(btn1, btn2)
            sent = send_msg(message=message,
                            how_many_message_to_del=2,
                            chat_id=message.chat.id,
                            text="Отправьте фотографию пж")
            bot.register_next_step_handler(sent, add_exercise_finish)

    # Старт
    add_exercise_type(message)


# Добавление домашки в банк
def add_homework(message: types.Message):
    homework = Homework()  # Создание объекта класса Homework

    # Запрос типа экзамена
    def add_homework_exam_type(message: types.Message):
        try:
            # Создание клавиатуры, добавление кнопок
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                           one_time_keyboard=True,
                                           input_field_placeholder="ПРОФИЛЬ/БАЗА/ОГЭ")
            btn1 = types.KeyboardButton("ПРОФИЛЬ")
            btn2 = types.KeyboardButton("БАЗА")
            btn3 = types.KeyboardButton("ОГЭ")
            kb.add(btn1, btn2, btn3)

            # Бот запрашивает тип экзамена для дз и регистрирует следующее сообщение
            sent = send_msg(message=message,
                            how_many_message_to_del=2,
                            chat_id=message.chat.id,
                            text="ДЗ какого экзамена?",
                            reply_markup=kb
                            )
            bot.register_next_step_handler(sent, add_homework_type)
        except Exception as error:
            logger.error(error)

    def add_homework_type(message: types.Message):
        nonlocal homework
        # Запись ответа в объект класса дз
        homework.exam_type = message.text
        # Создание клавиатуры, добавление кнопок
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                       one_time_keyboard=True,
                                       input_field_placeholder="1 / 2")
        btn1 = types.KeyboardButton("1")
        btn2 = types.KeyboardButton("2")
        kb.add(btn1, btn2)

        # Бот запрашивает, из какой части экзамена дз, и регистрирует следующее сообщение
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="ДЗ для 1 или 2 части экзамена?"
                        )
        bot.register_next_step_handler(sent, add_homework_answers)

    # Регистрация ответов на дз
    def add_homework_answers(message: types.Message):
        nonlocal homework
        homework.hw_type = message.text
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Отправьте ответы на 1 часть (1 номер = 1 строка)\nЕсли это 2 часть отправьте  '-'",
                        )
        bot.register_next_step_handler(sent, add_homework_file)

    def add_homework_file(message: types.Message):
        nonlocal homework
        homework.right_answers = message.text if message.text != '-' else None
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Пришлите файл")
        bot.register_next_step_handler(sent, add_homework_finish)

    def add_homework_finish(message: types.Message):
        nonlocal homework
        try:
            homework.file_id = message.document.file_id
            with conn:
                homework.save(force_insert=True)
            kb = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("В меню", callback_data="teacher menu")
            btn2 = types.InlineKeyboardButton(
                "Добавить дз", callback_data="new homework"
            )
            kb.add(btn1, btn2)
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=message.chat.id,
                     text=f"Успешно добавлено\n"
                          f"Экзамен:{homework.exam_type}\n"
                          f"ДЗ номер N:{homework.hw_id}\n",
                     reply_markup=kb,
                     )
        except Exception as error:
            logger.error(error)
            sent = send_msg(message=message,
                            how_many_message_to_del=2,
                            chat_id=message.chat.id,
                            text="Ошибка. Отправьте файл пж")
            bot.register_next_step_handler(sent, add_homework_finish)

    add_homework_exam_type(message)


# Добавление варианта в Банк
def add_test(message: types.Message):
    test = Test()

    def add_test_type(message: types.Message):
        try:
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                           input_field_placeholder="ПРОФИЛЬ/БАЗА/ОГЭ")
            btn1 = types.KeyboardButton("ПРОФИЛЬ")
            btn2 = types.KeyboardButton("БАЗА")
            btn3 = types.KeyboardButton("ОГЭ")
            kb.add(btn1, btn2, btn3)
            sent = send_msg(message=message,
                            how_many_message_to_del=2,
                            chat_id=message.chat.id,
                            text="Вариант какого экзамена?",
                            reply_markup=kb
                            )
            bot.register_next_step_handler(sent, add_test_answers)
        except Exception as error:
            logger.error(error)

    def add_test_answers(message: types.Message):
        nonlocal test
        test.exam_type = message.text
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Отправьте ответы на 1 часть (1 номер = 1 строка)",
                        reply_markup=types.ReplyKeyboardRemove(),
                        )
        bot.register_next_step_handler(sent, add_test_file)

    def add_test_file(message: types.Message):
        nonlocal test
        test.answers_1part = message.text
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Пришлите файл")
        bot.register_next_step_handler(sent, add_test_finish)

    def add_test_finish(message: types.Message):
        nonlocal test
        answers = test.answers_1part.split()
        try:
            test.file_id = message.document.file_id
            with conn:
                test.save(force_insert=True)
            kb = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("В меню", callback_data="teacher menu")
            btn2 = types.InlineKeyboardButton(
                "Добавить вариант", callback_data="new homework"
            )
            kb.add(btn1, btn2)
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=message.chat.id,
                     text=f"Успешно добавлено\n"
                          f"Экзамен:{test.exam_type}\n"
                          f"Вариант N:{test.test_id}\n"
                          f"Ответы первой части:\n"
                          + "\n".join([f"{i + 1}. {answers[i]}" for i in range(len(answers))]),
                     reply_markup=kb,
                     )
        except Exception as error:
            print("add_test_finish", error)
            sent = send_msg(message=message,
                            how_many_message_to_del=2,
                            chat_id=message.chat.id,
                            text="Ошибка. Отправьте файл пж")
            bot.register_next_step_handler(sent, add_test_finish)

    add_test_type(message)


# Рассылка новых видео школьникам
def sender(message: types.Message):
    """Рассылка ученикам на курсе"""

    def get_text(message: types.Message):
        # Создание клавиатуры, добавление кнопки ОТМЕНА
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Отмена", callback_data="teacher menu"))

        # Запрос текста рассылки
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Пришлите текст для рассылки",
                        reply_markup=kb)
        bot.register_next_step_handler(sent, send_url_for_students)

    def send_url_for_students(message: types.Message):
        text = message.text
        # Достаём из БД всех курсовиков
        with conn:
            users = [i for i in User.select().where(User.if_get_course != 0).execute()]

        # Рассылка пользователям
        for i in users:
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=i.user_id,
                     text="Новое сообщение от учителя:\n" + text)

    get_text(message)


# Отправка статистики по всем ученикам в виде excel таблицы
def students_statistic(message: types.Message):
    make_excel()
    file = open("statistic.xlsx", "rb")
    bot.send_document(
        chat_id=message.chat.id,
        document=file,
        visible_file_name="Файл со всей статистикой учеников.xlsx",
    )
    # Финиш


# Получение пробника на проверку
def test_checking_menu(message: types.Message):
    # Проверка наличия вариантов
    try:
        with conn:
            user_test = UserTestResult.get_or_none(
                UserTestResult.teacher_file_id is None)  # Получение пробников, 2 часть которых не проверена
        if user_test:
            kb = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton(text="В меню", callback_data="menu")
            btn2 = types.InlineKeyboardButton(text="Cдать проверку",
                                              callback_data=f"submit test checking,{user_test.result_id}")
            kb.add(btn1, btn2)
            # Отправка пробника
            photos = user_test.student_file_id.split()
            if len(photos) == 1:
                bot.send_photo(chat_id=message.chat.id,
                               photo=photos[0])
            else:
                for i, v in enumerate(photos):
                    photos[i] = types.InputMediaPhoto(media=v)
                bot.send_media_group(chat_id=message.chat.id,
                                     media=photos)
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=message.chat.id,
                     text=f"Текущий пробник на ответ. ЗА 1 часть получено {user_test.points_of_1_part} баллов",
                     reply_markup=kb)
        else:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text="В меню", callback_data="teacher menu"))
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=message.chat.id,
                     text="Ответов пока нет",
                     reply_markup=kb)

    except Exception as e:
        logger.error(e)
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="В меню", callback_data="teacher menu"))
        send_msg(message=message,
                 how_many_message_to_del=2,
                 chat_id=message.chat.id,
                 text="Ответов пока нет",
                 reply_markup=kb)


def submit_test_check(message: types.Message, result_id: int):
    with conn:
        user_test = UserTestResult.get(result_id=result_id)

    def get_points(message: types.Message):
        sent = send_msg(message=message,
                        how_many_message_to_del=2, chat_id=message.chat.id,
                        text="Во сколько баллов оцениваете решение")
        bot.register_next_step_handler(sent, get_test_file)

    def get_test_file(message: types.Message):
        nonlocal user_test
        user_test.points_of_2_part = int(message.text)
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Пришлите файл")
        bot.register_next_step_handler(sent, save_test_results)

    def save_test_results(message: types.Message):
        nonlocal user_test
        try:
            user_test.teacher_file_id = message.document.file_id
            with conn:
                user_test.save(force_insert=True)
            kb = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("В меню", callback_data="teacher menu")
            btn2 = types.InlineKeyboardButton("Проверить ещё", callback_data="check test")
            kb.add(btn1, btn2)
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=message.chat.id,
                     text=f"Успешно добавлено\n",
                     reply_markup=kb)
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=user_test.user_id,
                     text="Твой пробник уже проверен! Айда глянем, насколько хорошо ты с ним справился")
        except Exception as error:
            logger.error(error)
            sent = send_msg(message=message,
                            how_many_message_to_del=2,
                            chat_id=message.chat.id,
                            text="Ошибка. Отправьте файл заново пж")
            bot.register_next_step_handler(sent, save_test_results)

    get_points(message=message)


# Получение дз на проверку
def homework_checking_menu(message: types.Message):
    # Проверка наличия вариантов
    try:
        with conn:
            # Получение пробников, 2 часть которых не проверена
            user_test = UserHomeworkResult.get_or_none(UserHomeworkResult.teacher_file_id is None,
                                                       UserHomeworkResult.student_file_id is not None)
            user = User.get(user_id=user_test.user_id)

        if user_test:
            kb = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton(text="В меню", callback_data="teacher menu")
            btn2 = types.InlineKeyboardButton(text="Cдать проверку",
                                              callback_data=f"submit homework checking,{user_test.result_id}")
            kb.add(btn1, btn2)
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=message.chat.id,
                     text=f"Текущее дз на ответ от {user.name} {user.lastname} {user.if_get_course}",
                     reply_markup=kb)

            # Отправка пробника
            photos = user_test.student_file_id.split()
            if len(photos) == 1:
                bot.send_photo(chat_id=message.chat.id,
                               photo=photos[0])
            else:
                for i, v in enumerate(photos):
                    photos[i] = types.InputMediaPhoto(media=v)
                bot.send_media_group(chat_id=message.chat.id,
                                     media=photos)
        else:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text="В меню", callback_data="teacher menu"))
            send_msg(message=message,
                     how_many_message_to_del=2, chat_id=message.chat.id,
                     text="Ответов пока нет",
                     reply_markup=kb)
    except Exception as e:
        logger.error(e)
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="В меню", callback_data="teacher menu"))
        send_msg(message=message,
                 how_many_message_to_del=2, chat_id=message.chat.id,
                 text="Ответов пока нет",
                 reply_markup=kb)


def submit_homework_check(message: types.Message, result_id: int):
    with conn:
        user_test = UserHomeworkResult.get(result_id=result_id)

    def get_points(message: types.Message):
        sent = send_msg(message=message,
                        how_many_message_to_del=2, chat_id=message.chat.id,
                        text="Во сколько баллов оцениваете решение")
        bot.register_next_step_handler(sent, get_hw_file)

    def get_hw_file(message: types.Message):
        nonlocal user_test
        user_test.points = int(message.text)
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Пришлите файл")
        bot.register_next_step_handler(sent, save_hw_results)

    def save_hw_results(message: types.Message):
        nonlocal user_test
        try:
            user_test.teacher_file_id = message.document.file_id
            with conn:
                user_test.save()
            kb = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("В меню", callback_data="teacher menu")
            btn2 = types.InlineKeyboardButton("Проверить ещё", callback_data="check homework")
            kb.add(btn1, btn2)
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=message.chat.id,
                     text=f"Успешно добавлено",
                     reply_markup=kb)
            send_msg(message=message,
                     how_many_message_to_del=2, chat_id=user_test.user_id,
                     text="Твоё дз уже проверено! Айда глянем, насколько хорошо ты с ним справился")
        except Exception as error:
            logger.error(error)
            sent = send_msg(message=message,
                            how_many_message_to_del=2,
                            chat_id=message.chat.id,
                            text="Ошибка. Отправьте файл пж")
            bot.register_next_step_handler(sent, save_hw_results)

    get_points(message=message)


def answer(message: types.Message, answer_from: str, user_id: int):
    def get_answer(message: types.Message):
        send_msg(message=message,
                 how_many_message_to_del=2,
                 chat_id=message.chat.id,
                 text="Введите ответное сообщение")
        bot.register_next_step_handler_by_chat_id(message.chat.id,
                                                  is_valid_message)

    def is_valid_message(message: types.Message):
        logger.info(f"{answer_from} {message.text}")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                       one_time_keyboard=True)
        btn1 = types.KeyboardButton(text='✅')
        btn2 = types.KeyboardButton(text='❎')
        kb.add(btn1, btn2)
        bot.copy_message(chat_id=message.chat.id,
                         from_chat_id=message.chat.id,
                         message_id=message.message_id,
                         reply_markup=kb)
        bot.register_next_step_handler_by_chat_id(message.chat.id, send_answer)

    def send_answer(message: types.Message):
        logger.info(message.text)
        match message.text:
            case '✅':
                send_msg(message=message,
                         how_many_message_to_del=2, chat_id=message.chat.id, text="Принял понял")
                send_msg(message=message,
                         how_many_message_to_del=0, chat_id=user_id, text=f"Ответ от {answer_from}")
                bot.copy_message(chat_id=user_id,
                                 from_chat_id=message.chat.id,
                                 message_id=message.message_id - 1)
            case _:
                get_answer(message)

    logger.info('ВХОД', message.json)
    get_answer(message)


def send_database(message: types.Message):
    db = open("data.db", 'rb')
    bot.send_document(chat_id=message.chat.id,
                      document=db)


"""Часть для учеников"""


# РЕГИСТРАЦИЯ
def registration(message: types.Message):
    user = User()

    # Регистрация имени и фамилии
    def start_registration(message: types.Message):
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Напиши своё Имя и Фамилию")
        bot.register_next_step_handler(sent, select_course)

    # Регистрация курса
    def select_course(message: types.Message):
        nonlocal user
        try:
            user.user_id = message.chat.id
            user.name, user.lastname = message.text.split()
        except Exception as e:
            logger.error(e)
            user.name = message.text
            user.lastname = message.from_user.username

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True,
                                       input_field_placeholder="ПРОФИЛЬ/БАЗА/ОГЭ")
        btn1 = types.KeyboardButton(text="ОГЭ")
        btn2 = types.KeyboardButton(text="ПРОФИЛЬ")
        btn3 = types.KeyboardButton(text="БАЗА")
        kb.add(btn1, btn2, btn3)
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Что сдаёшь?",
                        reply_markup=kb)
        bot.register_next_step_handler(sent, finish_registration)

    # Сохранение данных в БД, переход в меню
    def finish_registration(message: types.Message):
        # Проверка в группах учеников: 0 - нигде нет, 1 - душный курс, 2 - недушный курс
        nonlocal user

        user.exam_type = message.text

        try:
            if bot.get_chat_member(chat_id=int(os.getenv("STUFFY_COURSE")), user_id=user.user_id).status == "member":
                user.if_get_course = 1
            if bot.get_chat_member(chat_id=int(os.getenv("NO_STUFFY_COURSE")), user_id=user.user_id).status == "member":
                user.if_get_course = 2
            else:
                user.if_get_course = 0
        except Exception as e:
            logger.error(e)
            user.if_get_course = 0

        with conn:
            m = user.save(force_insert=True)
            logger.debug(m)
            logger.debug(user.view())

        send_msg(message=message,
                 how_many_message_to_del=2,

                 chat_id=message.chat.id,
                 text="Поздравляю, регистрация пройдена успешно! "
                      "\nУспешного обучения и высоких баллов")
        kb = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(text="В меню", callback_data="student menu")
        kb.add(btn1)

        send_msg(message=message,
                 how_many_message_to_del=0,
                 chat_id=message.chat.id,
                 text="Перейдём в меню?",
                 reply_markup=kb)
        # Окончание регистрации

    # Проверка подписки на основной канал
    try:
        is_member = bot.get_chat_member(chat_id="@dushnilamath", user_id=message.chat.id)
        if is_member.status == "left":
            raise Exception
        start_registration(message)
    except Exception as error:  # Если не подписан, регистрация не начинается
        kb = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(
            text="Подписаться", url="https://t.me/dushnilamath"
        )
        btn2 = types.InlineKeyboardButton(
            text="Регистрация", callback_data="registration"
        )
        kb.add(btn1, btn2)
        try:
            bot.edit_message_text(
                f"Подпишись пж {error}",
                message.chat.id,
                message.message_id,
                reply_markup=kb,
            )
        except Exception as e:
            print(e)


# Меню для учеников
def student_menu(message: types.Message):
    # Создание объекта класса User с данными из БД по первичному ключу - user id
    with conn:
        user = User.get_or_none(User.user_id == message.chat.id)
    # Создание клавиатуры
    kb = types.InlineKeyboardMarkup(row_width=1)

    # Меню для пользователей
    # Создание кнопок
    btn1 = types.InlineKeyboardButton("Моя статистика", callback_data="profile")
    btn2 = types.InlineKeyboardButton("Порешать задания", callback_data="do exercises")
    btn3 = types.InlineKeyboardButton("Решить вариант", callback_data="do test")
    kb.add(btn1)
    kb.row(btn2, btn3)
    # Дополнительные функции ученикам Душный и недушный курсов
    if user.if_get_course >= 1:
        btn4 = types.InlineKeyboardButton("ДЗ", callback_data="do homework")
        btn5 = types.InlineKeyboardButton("Написать преподу", callback_data="chat with teacher")
        btn7 = types.InlineKeyboardButton("Вся теория", callback_data="theory")
        kb.add(btn4, btn5, btn7)
    # Ученикам без курса предлагается его купить
    btn8 = types.InlineKeyboardButton("магазин курсов", callback_data="course_shop")
    btn6 = types.InlineKeyboardButton("Написать в техподдержку", callback_data="SOS")
    kb.add(btn8, btn6)
    # Вывод меню
    try:
        bot.edit_message_text(
            f"Что сделаем, {user.name}?",
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=kb,
        )
    except Exception as e:
        logger.error(e)
        send_msg(message=message,
                 how_many_message_to_del=2,
                 chat_id=message.chat.id,
                 text="Что сделаем, {user.name}?",
                 reply_markup=kb)


# Меню профиля пользователя
def profile(message: types.Message):
    # Создание объекта класса User с данными из БД по первичному ключу - user id
    with conn:
        user = User.get(User.user_id == message.chat.id)

    # Создание клавиатуры
    kb = types.InlineKeyboardMarkup()

    # Создание кнопок
    btn1 = types.InlineKeyboardButton("Купить курс", url="https://clck.ru/355ikC")
    btn2 = types.InlineKeyboardButton("В меню", callback_data="student menu")

    # Текст со статистикой ученика для сообщения
    text_for_bot = f"""
    Пользователь N: {user.user_id}
    \nИмя: {user.name}
    \nСтатистика решённых заданий: 
    \n\t{(user.correct_ex / user.total_ex) * 100 if user.total_ex != 0 else 0} % ({user.correct_ex} из {user.total_ex})
    \nСтатистика вариантов: 
    \n\tВ среднем {(user.total_points / (user.total_tests * 100)) * 100 if user.total_tests != 0 else 0} за тест
    \n\tНаибольший балл за вариант - {user.max_points_per_test}
    \n\tВсего решено {user.total_tests} варианта"""

    # Дополнение к тексту для тех, кто не купил курс
    if user.if_get_course == 0:
        text_for_bot += "\n\nХочешь улучшить свой балл? Го на курс!"
        kb.add(btn1)
    kb.add(btn2)

    # Вывод профиля ученика
    bot.edit_message_text(
        text=text_for_bot,
        chat_id=message.chat.id,
        message_id=message.message_id,
        reply_markup=kb,
    )


# Меню с заданиями
def exercise_menu(message: types.Message, page: int = 1, num: int = 1):
    # Создание объекта класса User с данными из БД по первичному ключу - user id
    with conn:
        user = User.get(user_id=message.chat.id)
        examtype = ExamType.get(exam_type=user.exam_type)
        ex_list = [i for i in Exercise.select().where(Exercise.exam_type == user.exam_type)]

    def select_number(message: types.Message):
        nonlocal user, examtype
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                       one_time_keyboard=True)

        btn = [types.KeyboardButton(str(i)) for i in range(1, examtype.number_of_questions + 1)]
        kb.add(*btn)
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text=f"Экзамен: {user.exam_type}\nКакой номер задания хочешь поботать? Пришли номер задания",
                        reply_markup=kb
                        )
        bot.register_next_step_handler(sent, get_ex)

    def get_ex(message: types.Message):
        try:
            nonlocal user, ex_list

            test_num = int(message.text) if message.text else num

            ex_list = [i for i in ex_list if i.number_of_ex_in_test == test_num]

            kb = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton(text="В меню", callback_data="student menu")
            kb.add(btn1)

            left = page - 1 if page != 1 else len(ex_list)
            right = page + 1 if page != len(ex_list) else 1

            left_button = types.InlineKeyboardButton("←", callback_data=f'exercise to,{test_num},{left}')
            page_button = types.InlineKeyboardButton(f"{page}/{len(ex_list)}", callback_data='student menu')
            right_button = types.InlineKeyboardButton("→", callback_data=f'exercise to,{test_num},{right}')
            kb.add(left_button, page_button, right_button)

            bot.send_photo(
                chat_id=message.chat.id,
                photo=ex_list[page - 1].file_id,
                caption=f"Ответ: <tg-spoiler>{ex_list[page - 1].right_answer}</tg-spoiler>",
                parse_mode="HTML",
                reply_markup=kb,
            )
            bot.delete_message(chat_id=message.chat.id,
                               message_id=message.message_id - 1)
            bot.delete_message(chat_id=message.chat.id,
                               message_id=message.message_id)

        except Exception as e:
            logger.error(e)
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text="В меню", callback_data="student menu"),
                   types.InlineKeyboardButton(text="Выбрать другой прототип", callback_data="do exercises"))
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=message.chat.id,
                     text="Заданий этого типа у меня ещё нет",
                     reply_markup=kb)

    if page == 1:
        select_number(message)
    else:
        get_ex(message)


# Выбор пробника
def test_menu(message: types.Message, page: int = 1):
    # Проверка наличия вариантов
    try:
        with conn:
            user = User.get(user_id=message.chat.id)  # Получение данных о пользователе
            tests = [i for i in Test.select().where(Test.exam_type == user.exam_type).order_by(
                Test.test_id.desc()).execute()]  # получение пробников с типом экзамена юзера
            test = tests[page - 1]  # Текущий пробник на вывод
            user_test = UserTestResult.get_or_none(user_id=user.user_id,
                                                   test_id=test.test_id)

        kb = types.InlineKeyboardMarkup()

        left = page - 1 if page != 1 else len(tests)
        right = page + 1 if page != len(tests) else 1

        left_button = types.InlineKeyboardButton("←", callback_data=f'test to,{left}')
        page_button = types.InlineKeyboardButton(f"{str(page)}/{str(len(tests))}", callback_data='student menu')
        right_button = types.InlineKeyboardButton("→", callback_data=f'test to,{right}')
        kb.add(left_button, page_button, right_button)

        btn1 = types.InlineKeyboardButton(text="В меню", callback_data="student menu")
        if not user_test:
            btn2 = types.InlineKeyboardButton(text="Cдать ответы", callback_data=f"submit test answers,{test.test_id}")
        else:
            btn2 = types.InlineKeyboardButton(text="К результатам", callback_data=f"send test result,{test.test_id}")
        kb.add(btn1, btn2)

        # Отправка варианта
        bot.send_document(
            chat_id=message.chat.id,
            document=test.file_id,
            caption=f"Удачи!\n"
                    f"Экзамен:{test.exam_type}\n"
                    f"Вариант N:{test.test_id}\n",
            visible_file_name=f"Вариант номер {test.test_id} по {test.exam_type}",
            reply_markup=kb
        )
        bot.delete_message(chat_id=message.chat.id,
                           message_id=message.message_id)

    except Exception as e:
        logger.error(e)
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="В меню", callback_data="student menu"))
        send_msg(message=message,
                 chat_id=message.chat.id,
                 text="Вариантов пока нет",
                 reply_markup=kb)


# Сдача ответов пробника
def submit_test_answers(message: types.Message, test_id: int):
    user_test = UserTestResult(test_id=test_id)

    def submit_1part_answers(message: types.Message):
        try:
            text = """Пришли ответы *1 сообщением*, используя 1 строку как ответ на 1 вопрос, как в примере
    Пример сообщения:
    12
    -34
    56
    ...
    Будет распознано так:
    1 задание - *12*
    2 задание - *-34*
    3 задание - *56*
    и т.д."""
            sent = send_msg(message=message,
                            how_many_message_to_del=2,

                            chat_id=message.chat.id,
                            text=text,
                            parse_mode='Markdown'
                            )
            bot.register_next_step_handler(sent, save_1part)
        except Exception as e:
            logger.error(e)

    def save_1part(message: types.Message):
        nonlocal user_test
        with conn:
            test = Test.get(test_id=test_id)
            user = User.get(user_id=message.chat.id)

        user_test.user_id = user.user_id
        user_test.exam_type = user.exam_type

        try:  # Получение ответов от пользователя
            user_answers = (message.text.split())  # конвертация строки с ответами пользователя-> список
            test_answers = (test.answers_1part.split())  # Получение правильных ответов из БД
            map(int, user_answers)  # проверка на числовое значение
            # Алгоритм сверяет ответы
            k = ["❌"] * len(test_answers)
            for i in range(len(test_answers)):
                try:
                    if user_answers[i] == test_answers[i]:
                        k[i] = "✅"  # Отмечается правильным, если элементы совпадают
                except IndexError:
                    user_answers.append("-")  # Если ученик сдал не все ответы,
            # Сохранение результатов
            user_test.answers_1part = " ".join(user_answers)  # Сохранение строки с ответами в БД
            user_test.result_1part = " ".join(k)  # Сохранение строки с результатом проверки в БД
            user_test.points_of_1_part = k.count("✅")  # Сохранение количества набранных баллов за 1 часть

            if user.if_get_course in (0, 1):
                approve_answers(message)
            else:
                submit_2part_answers(message)
        except Exception as e:
            logger.error(e)
            sent = send_msg(message=message,
                            how_many_message_to_del=2,

                            chat_id=message.chat.id,
                            text="Произошла Ошибка. Пришли ответы как в примере ещё раз")
            bot.register_next_step_handler(sent, submit_1part_answers)

    def submit_2part_answers(message: types.Message):
        """Поучение от пользователя фотографий с его решением 2 части"""
        nonlocal user_test
        user_test.student_file_id = ""

        kb = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        kb.add(types.KeyboardButton(text='СТОП'))

        sent = send_msg(message=message,
                        how_many_message_to_del=2,

                        chat_id=message.chat.id,
                        text="""Пришли следующим сообщением фотографии решения 2 части.
            Важно присылай их по 1 (1 сообщение = 1 фото), чтобы я правильно их принял. 
            Когда закончишь присылать фотографии - напиши СТОП""",
                        reply_markup=kb)
        bot.register_next_step_handler(sent, save_2part)

    def save_2part(message: types.Message):
        nonlocal user_test
        try:
            sent = send_msg(message=message,
                            how_many_message_to_del=2,
                            chat_id=message.chat.id,
                            text="Принял")
            if message.photo:
                user_test.student_file_id += f"{message.photo[-1].file_id} "
                bot.register_next_step_handler(sent, save_2part)
            elif message.text == "СТОП" or len(user_test.student_file_id.split()) == 10:
                approve_answers(message)

        except Exception as e:
            print("save_2part", e)
            sent = send_msg(message=message,
                            how_many_message_to_del=2,
                            chat_id=message.chat.id,
                            text="Отправь фотки заново, пж")
            bot.register_next_step_handler(sent, save_2part)

    def approve_answers(message: types.Message):
        nonlocal user_test
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                       one_time_keyboard=True,
                                       input_field_placeholder='Используйте кнопки')
        btn1 = types.KeyboardButton("Да")
        btn2 = types.KeyboardButton("Ввести всё заново")
        kb.add(btn1, btn2)
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text="Подтвердите ваши ответы\n" +
                             "N | Твой ответ\n" +
                             "".join(
                                 [f"{index + 1}.  {item}\n" for index, item in
                                  enumerate(user_test.answers_1part.split())]),
                        reply_markup=kb)
        logger.info(sent.text)
        bot.register_next_step_handler(sent, save_results)

    def save_results(message: types.Message):
        nonlocal user_test
        try:
            if message.text == "Да":
                with conn:
                    user_test.save(force_insert=True)
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("К результатам", callback_data=f"send test result, {test_id}"))
                send_msg(message=message,
                         how_many_message_to_del=2,
                         chat_id=message.chat.id,
                         text="Успешно добавлено! А я уже знаю твои баллы за 1 часть, хочешь покажу ↓↓↓",
                         reply_markup=kb)
            else:
                submit_1part_answers(message=message)
        except Exception as e:
            logger.error(e)
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=message.chat.id,
                     text="Произошла ошибка, попробуйте ввести ответы снова")
            submit_1part_answers(message=message)

    # Запуск
    submit_1part_answers(message)


# Вывод результатов пробника
def send_test_results(message: types.Message, test_id: int):
    with conn:
        user_test = UserTestResult.get(test_id=test_id, user_id=message.chat.id)
        test = Test.get(test_id=test_id)

    test_answers = test.answers_1part.split()
    user_answers = user_test.answers_1part.split()
    user_results_1part = user_test.result_1part.split()
    user_points = user_test.points_of_1_part
    text = f"Результаты 1 части - набрано {user_points} балла\n     N Твой ответ\n"
    for i, (test_answer, user_answer, res) in enumerate(zip(test_answers, user_answers, user_results_1part)):
        text += f"`{res}{i + 1}. {user_answer} (Ответ: {test_answer})\n`" if res == "❌" \
            else f"`{res}{i + 1}. {user_answer}\n`"
    send_msg(message=message,
             how_many_message_to_del=2,
             chat_id=message.chat.id,
             text=text,
             parse_mode='Markdown')

    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("В меню", callback_data="student menu")
    kb.add(btn1)
    if user_test.teacher_file_id:
        bot.send_document(
            chat_id=message.chat.id,
            document=user_test.teacher_file_id,
            caption=f"Результат проверки 2 части: {user_test.points_of_2_part} баллов",
            visible_file_name=f"{user_test.user_id} 2 часть {test.test_id}",
            reply_markup=kb
        )
    else:
        send_msg(message=message,
                 how_many_message_to_del=2,

                 chat_id=message.chat.id,
                 text="2 часть ещё не проверена",
                 reply_markup=kb
                 )


# Выбор пробника
def homework_menu(message: types.Message, page: int = 1):
    # Проверка наличия вариантов
    try:
        with conn:
            user = User.get(user_id=message.chat.id)  # Получение данных о пользователе
            homework_list = [i for i in Homework.select().where(Homework.exam_type == user.exam_type).order_by(
                Homework.hw_id.desc()).execute()]  # получение hw с типом экзамена юзера
            homework = homework_list[page - 1]  # Текущий hw на вывод
            user_homework = UserHomeworkResult.get_or_none(user_id=user.user_id,
                                                           hw_id=homework.hw_id)

        kb = types.InlineKeyboardMarkup()

        left = page - 1 if page != 1 else len(homework_list)
        right = page + 1 if page != len(homework_list) else 1

        left_button = types.InlineKeyboardButton("←", callback_data=f'homework to,{left}')
        page_button = types.InlineKeyboardButton(f"{str(page)}/{str(len(homework_list))}", callback_data='student menu')
        right_button = types.InlineKeyboardButton("→", callback_data=f'homework to,{right}')
        kb.add(left_button, page_button, right_button)

        btn1 = types.InlineKeyboardButton(text="В меню", callback_data="student menu")
        if not user_homework:
            btn2 = types.InlineKeyboardButton(text="Cдать ответы",
                                              callback_data=f"submit homework answers,{homework.hw_id}")
        else:
            btn2 = types.InlineKeyboardButton(text="К результатам",
                                              callback_data=f"send homework result,{homework.hw_id}")
        kb.add(btn1, btn2)

        # Отправка варианта
        bot.send_document(
            chat_id=message.chat.id,
            document=homework.file_id,
            caption=f"Удачи!\n"
                    f"Экзамен:{homework.exam_type}\n"
                    f"ДЗ N:{homework.hw_id}\n",
            reply_markup=kb
        )
        bot.delete_message(chat_id=message.chat.id,
                           message_id=message.message_id)

    except Exception as e:
        logger.error(e)
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="В меню", callback_data="student menu"))
        send_msg(message=message,
                 how_many_message_to_del=2,
                 chat_id=message.chat.id,
                 text="ДЗ пока нет",
                 reply_markup=kb)


# Сдача ответов hw
def submit_homework_answers(message: types.Message, hw_id: int):
    user_homework = UserHomeworkResult(hw_id=hw_id)

    def submit_1part_answers(message: types.Message):
        try:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text="В меню", callback_data="student menu"))
            text = """Пришли ответы *1 сообщением*, используя 1 строку как ответ на 1 вопрос, как в примере
        Пример сообщения:
        12
        -34
        56
        ...
        Будет распознано так:
        1 задание - *12*
        2 задание - *-34*
        3 задание - *56*
        и т.д."""
            sent = send_msg(message=message,
                            how_many_message_to_del=2,
                            chat_id=message.chat.id,
                            text=text,
                            parse_mode='Markdown',
                            reply_markup=kb
                            )
            bot.register_next_step_handler(sent, save_1part)
        except Exception as e:
            logger.error(e)

    def save_1part(message: types.Message):
        nonlocal homework, homework, user

        try:  # Получение ответов от пользователя
            user_answers = (message.text.split())  # конвертация строки с ответами пользователя-> список
            hw_answers = (homework.right_answers.split())  # Получение правильных ответов из БД
            map(int, user_answers)  # проверка на числовое значение
            # Алгоритм сверяет ответы
            k = ["❌"] * len(hw_answers)
            for i in range(len(hw_answers)):
                try:
                    if user_answers[i] == hw_answers[i]:
                        k[i] = "✅"  # Отмечается правильным, если элементы совпадают
                except IndexError:
                    user_answers.append("-")  # Если ученик сдал не все ответы,
            # Сохранение результатов
            user_homework.answers_1part = " ".join(user_answers)  # Сохранение строки с ответами в БД
            user_homework.result_1part = " ".join(k)  # Сохранение строки с результатом проверки в БД
            user_homework.points = k.count("✅")  # Сохранение количества набранных баллов за 1 часть
            approve_answers(message)
        except Exception as e:
            logger.error(e)
            sent = send_msg(message=message,
                            how_many_message_to_del=2,

                            chat_id=message.chat.id,
                            text="Произошла Ошибка. Пришли ответы как в примере ещё раз")
            bot.register_next_step_handler(sent, submit_1part_answers)

    def submit_2part_answers(message: types.Message):
        """Поучение от пользователя фотографий с его решением 2 части"""
        nonlocal user_homework
        user_homework.student_file_id = ""

        kb = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        kb.add(types.KeyboardButton(text='СТОП'))

        sent = send_msg(message=message,
                        how_many_message_to_del=2,

                        chat_id=message.chat.id,
                        text="""Пришли следующим сообщением фотографии решения 2 части.
                Важно присылай их по 1 (1 сообщение = 1 фото), чтобы я правильно их принял. 
                Когда закончишь присылать фотографии - напиши СТОП""",
                        reply_markup=kb)
        bot.register_next_step_handler(sent, save_2part)

    def save_2part(message: types.Message):
        nonlocal user_homework
        try:
            if message.photo:
                user_homework.student_file_id += f"{message.photo[-1].file_id} "
                sent = send_msg(message=message,
                                how_many_message_to_del=2,
                                chat_id=message.chat.id,
                                text="Принял")
                bot.register_next_step_handler(sent, save_2part)
            elif message.text == "СТОП":
                approve_answers(message)

        except Exception as e:
            logger.error(e)
            sent = send_msg(message=message,
                            how_many_message_to_del=2,
                            chat_id=message.chat.id,
                            text="Отправь фотки заново, пж")
            bot.register_next_step_handler(sent, save_2part)

    def approve_answers(message: types.Message):
        nonlocal user_homework
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                       one_time_keyboard=True,
                                       input_field_placeholder='Используйте кнопки')
        btn1 = types.KeyboardButton("Да")
        btn2 = types.KeyboardButton("Отправить всё заново")
        kb.add(btn1, btn2)
        text = "Подтвердите ваши ответы\n"
        if user_homework.answers_1part:
            text += "N | Твой ответ\n"
            text += "".join(
                [f"{index + 1}.  {item}\n" for index, item in enumerate(user_homework.answers_1part.split())])
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text=text,
                        reply_markup=kb)
        bot.register_next_step_handler(sent, save_results)

    def save_results(message: types.Message):
        nonlocal user_homework
        try:
            if message.text == "Да":
                with conn:
                    user_homework.save(force_insert=True)
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("К результатам", callback_data=f"send homework result, {hw_id}"))
                send_msg(message=message,
                         how_many_message_to_del=2,
                         chat_id=message.chat.id,
                         text="Успешно добавлено! А я уже знаю твои баллы, хочешь покажу ↓↓↓",
                         reply_markup=kb)
            else:
                submit_homework_answers(message=message, hw_id=hw_id)
        except Exception as e:
            logger.error(e)
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=message.chat.id,
                     text="Произошла ошибка, попробуйте ввести ответы снова")
            submit_homework_answers(message=message, hw_id=hw_id)

    with conn:
        homework = Homework.get(hw_id=hw_id)
        user = User.get(user_id=message.chat.id)
        user_homework.user_id = user.user_id
        user_homework.exam_type = user.exam_type

    # Запуск
    if homework.hw_type == 1:
        submit_1part_answers(message)
    else:
        submit_2part_answers(message)


# Вывод результатов homework
def send_homework_results(message: types.Message, hw_id: int):
    with conn:
        user_homework = UserHomeworkResult.get(hw_id=hw_id,
                                               user_id=message.chat.id)
        homework = Homework.get(hw_id=hw_id)

    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("В меню", callback_data="student menu")
    kb.add(btn1)
    if homework.right_answers:
        homework_answers = homework.right_answers.split()
        user_answers = user_homework.answers_1part.split()
        user_results_1part = user_homework.result_1part.split()
        user_points = user_homework.points
        if homework.hw_type == 1:
            text = f"Результат дз - набрано {user_points} б.\n     N Твой ответ\n"
            for i, (test_answer, user_answer, res) in enumerate(
                    zip(homework_answers, user_answers, user_results_1part)):
                text += f"`{res}{i + 1}. {user_answer} (Ответ: {test_answer})\n`" if res == "❌" \
                    else f"`{res}{i + 1}. {user_answer}\n`"
            send_msg(message=message,
                     how_many_message_to_del=2,
                     chat_id=message.chat.id,
                     text=text,
                     parse_mode='Markdown',
                     reply_markup=kb)

    elif user_homework.teacher_file_id:
        bot.send_document(
            chat_id=message.chat.id,
            document=user_homework.teacher_file_id,
            caption=f"Результат проверки: {user_homework.points} баллов",
            visible_file_name=f"{user_homework.user_id} ДЗ {homework.hw_id}",
            reply_markup=kb
        )
    else:
        send_msg(message=message,
                 how_many_message_to_del=2,

                 chat_id=message.chat.id,
                 text="ДЗ ещё не проверена",
                 reply_markup=kb
                 )


def message_admin_menu(message: types.Message, mode):
    """Функция написать учителю. Запрашивает сообщение"""

    def get_msg(message: types.Message):
        if mode == "teacher":
            text = (
                "Возникли трудности в решении задачи? Напиши сообщение Олегу, надеюсь он поможет.\n"
                "Постарайся максимально объяснить ситуацию + постарайся предложить свой путь решения"
                "(Даже если тебе кажется, что это неверно)\n"
                "<tg-spoiler>А можешь просто похвалить за хорошую работу)</tg-spoiler>"
            )
        else:
            text = (
                "Что-то случилось? Опиши проблему максимально как можешь. Можешь также прикрепить фотографию\n"
                "<tg-spoiler>Техподдержка не помогает в решении задач и вариантов</tg-spoiler>"
            )
        # Создание клавиатуры и добавление кнопки "В меню"
        kb = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("В меню", callback_data="student menu")
        kb.add(btn1)
        # Запрос вопроса
        sent = send_msg(message=message,
                        how_many_message_to_del=2,
                        chat_id=message.chat.id,
                        text=text,
                        reply_markup=kb,
                        )
        # Регистрирует ответ пользователя на сообщение sent и передает в метод "message_to_teacher_2"
        bot.register_next_step_handler(sent, send_mes)

    def send_mes(message: types.Message):
        """Отправляет сообщения и предлагает выйти в меню"""

        # Отправляет сообщение в чат для учителя
        callback_text = (
            f"teacher answer,{message.chat.id}"
            if mode == "teacher"
            else f"support answer,{message.chat.id}"
        )

        kb = types.InlineKeyboardMarkup()
        btn2 = types.InlineKeyboardButton("Ответить", callback_data=callback_text)
        kb.add(btn2)
        bot.forward_message(
            chat_id=os.getenv("HELP_CHAT"),
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
        send_msg(message=message,
                 how_many_message_to_del=0,
                 chat_id=os.getenv("HELP_CHAT"),
                 text=f"Обращение от @{message.from_user.username} {message.chat.id} к {mode}",
                 reply_markup=kb)

        # Отправляет сообщение в чат ученика
        kb = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("В меню", callback_data="student menu")
        kb.add(btn1)
        send_msg(message=message,
                 how_many_message_to_del=2,

                 chat_id=message.chat.id,
                 text="Спасибо за обращение, постараемся ответить в максимально ближайшее время",
                 reply_markup=kb,
                 )

    get_msg(message)


def theory(message: types.Message):
    files_with_theory = [i for i in Theory.select().execute()]
    if not files_with_theory:
        send_msg(message=message,
                 how_many_message_to_del=2,
                 chat_id=message.chat.id,
                 text="Теория пока не добавлена")
    else:
        for i in files_with_theory:
            bot.send_document(chat_id=message.chat.id,
                              document=i.file_id,
                              caption=i.t_type)


def course_shop(message: types.Message):
    def f1(message: types.Message):
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        btn1 = types.KeyboardButton("Душный курс")
        btn2 = types.KeyboardButton("НЕдушный курс")
        btn3 = types.KeyboardButton("1 на 1")
        btn4 = types.KeyboardButton("Отмена, выйти в меню")
        kb.add(btn1, btn2, btn3, btn4)
        sent = bot.send_photo(chat_id=message.chat.id,
                              photo="AgACAgIAAxkBAAJfmGU-H43o--3jHkyqndviQpCt4ltBAAK-zjEbGfDwSX8zzKUI54VQAQADAgADdwADMAQ",
                              caption="Выбери курс",
                              reply_markup=kb)
        bot.register_next_step_handler(sent, f2)

    def f2(message: types.Message):
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        selected_course = message.text
        btns = (types.KeyboardButton("Месяц"),
                types.KeyboardButton("Год"))
        match selected_course:
            case "Душный курс":
                kb.add(btns[0], btns[1])
            case "НЕдушный курс":
                kb.add(btns[0], btns[1])
            case "1 на 1":
                kb.add(btns[0])
            case "Отмена, выйти в меню":
                student_menu(message)
        sent = bot.send_message(chat_id=message.chat.id,
                                text="Выберите режим",
                                reply_markup=kb)
        bot.register_next_step_handler(sent, f3, selected_course)

    def f3(message: types.Message, selected_course):
        mode = message.text
        bot.send_invoice(chat_id=message.chat.id, title=selected_course,
                         description=mode,
                         invoice_payload=f"{selected_course} {mode}",
                         provider_token=payments,
                         currency="RUB",
                         prices=[types.LabeledPrice("label", 123400)]
                         )
    f1(message)


@bot.pre_checkout_query_handler(func= lambda query: True)
def pre_checkout_query(p: types.PreCheckoutQuery):
    logger.debug(p)
    bot.answer_pre_checkout_query(p.id,True)

@bot.message_handler(content_types=types.SuccessfulPayment)
def successful_payment(message: types.Message):
    logger.debug(message)
    bot.send_message(message.chat.id,message.successful_payment)


def no_function(callback: types.CallbackQuery):
    """Функция вызывается, если выбранная на кнопках функция ещё не доработана"""
    bot.answer_callback_query(
        callback_query_id=callback.id,
        text="Эта функция ещё недоступна: скорее всего она дорабатывается",
        show_alert=True,
    )


@bot.message_handler(chat_types=["private"])
def echo(message: types.Message):
    """Эхо, если пользователь начнёт писать не вовремя"""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="В меню", callback_data="student menu"))

    bot.send_message(
        chat_id=message.chat.id,
        text="Я вас не понимаю, давайте перейдём в меню",
        reply_markup=kb)


def main():
    # Создание таблицы и объектов таблиц (моделей)
    on_start()
    # уведомляет о запуске бота
    on_starting()


if __name__ == "__main__":
    main()
    bot.infinity_polling(allowed_updates=telebot.util.update_types)
