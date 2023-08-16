import os
import random
import sqlite3

import telebot
from dotenv import load_dotenv
from telebot import types

from making_excel_with_statistic import make_excel


class User:
    '''Класс User - отвечает за данные пользователя'''

    def __init__(self, name: str = None, lastname: str = None,
                 telegram_id: int = 0,
                 exam_type: str = None,
                 if_get_course: int = 0,
                 total_ex: int = 0, correct_ex: int = 0,
                 total_tests: int = 0, total_points: int = 0,
                 most_points: int = 0):
        '''
        :param name: Имя пользователя
        :param lastname: Фамилия пользователя
        :param telegram_id: telegram id пользователя
        :param exam_type:'ПРОФИЛЬ'|'БАЗА'|'ОГЭ' - тип экзамена
        :param if_get_course: 0|1|2 - Купил ли пользователь курс: 0 - нет; 1 - душный курс; 2 - недушный курс
        # Далее данные, нужные для статистики
        :param total_ex: Сколько всего заданий пользователь решал
        :param correct_ex: Сколько всего заданий пользователь решил верно
        :param total_tests: Сколько всего вариантов решил пользователь
        :param total_points: Сколько суммарно набрал баллов
        :param most_points: Наивысший бал, набранный пользователем за 1 вариант
        '''
        self.telegram_id = telegram_id  # id пользователя в тг
        self.name = name  # Имя пользователя
        self.lastname = lastname  # Фамилия пользователя
        self.exam_type = exam_type  # Экзамен, который он/она будет сдавать: ОГЭ/ЕГЭ база/ЕГЭ профиль
        self.if_get_course = if_get_course  # Купил ли пользователь курс: 0 - нет; 1 - душный курс; 2 - недушный курс
        # Далее данные, нужные для статистики
        self.total_ex = total_ex  # Сколько всего заданий пользователь решал
        self.correct_ex = correct_ex  # Сколько всего заданий пользователь решил верно
        self.total_tests = total_tests  # Сколько всего вариантов решил пользователь
        self.total_points = total_points  # Сколько суммарно набрал баллов
        self.most_points = most_points  # Наивысший бал, набранный пользователем за 1 вариант


class DB:
    ''' Класс DB отвечает за связь (обмен данными) с Базой Данных (далее БД) '''

    def __init__(self, filename: str = 'database.db'):
        '''
        :param filename: Название файла БД
        '''
        self.filename = filename  # Имя файла с БД
        db = sqlite3.connect(self.filename)
        cursor = db.cursor()
        # Создание таблицы "users"
        cursor.execute('''CREATE TABLE IF NOT EXISTS users(
                            tg_user_id INTEGER PRIMARY KEY UNIQUE NOT NULL,
                            name TEXT,
                            lastname TEXT,
                            exam_type TEXT,
                            if_get_course INTEGER DEFAULT (0),
                            total_ex INTEGER DEFAULT (0),
                            correct_ex INTEGER DEFAULT (0),
                            total_tests INTEGER DEFAULT (0),
                            total_points INTEGER DEFAULT (0),
                            most_points INTEGER DEFAULT (0))''')

        # Создание таблицы "exercises"
        cursor.execute('''CREATE TABLE IF NOT EXISTS exercises(
                            ex_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            ex_file_id TEXT NOT NULL UNIQUE,
                            exam_type TEXT NOT NULL,
                            number_of_ex_in_test INTEGER NOT NULL,                      
                            right_answer TEXT NOT NULL,
                            total_attempts INTEGER,
                            right_attempts INTEGER);''')

        # Создание таблицы "tests"
        cursor.execute('''CREATE TABLE IF NOT EXISTS tests(
                                    test_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                    test_file_id TEXT NOT NULL UNIQUE,
                                    exam_type TEXT NOT NULL,                      
                                    right_answers TEXT NOT NULL,
                                    total_attempts INTEGER,
                                    most points INTEGER);''')

        # Надо ешё создать таблицы с ДЗ, Банком Вариантов и тд
        cursor.close()
        db.close()

    # Добавление или Обновление данных
    def add_info(self, request: str, values: list):
        """Метод для добавления или обновления данных в БД
        :param request: SQL запрос
        :param values: Значения"""

        connection = sqlite3.connect(self.filename)  # Подключение к БД
        cursor = connection.cursor()  # Создание курсора

        try:
            cursor.execute(request, values)  # Сам запрос
            connection.commit()  # Обновление БД
        except sqlite3.Error as error:
            # В случае ошибки не прекращается работа программы, а в консоль лишь выводится причина ошибка
            print(error)
        finally:  # В конце закрывает и курсор и подключение к БД
            cursor.close()
            connection.close()

    def select_info(self, request: str, values: list):
        '''
        Общий метод для взятия данных с БД
        :return: list - полученные данные
        :param request: SQL запрос
        :param values: значения для фильтрации полей
        '''
        connection = sqlite3.connect(self.filename)
        cursor = connection.cursor()
        try:
            cursor.execute(request, values)
            return cursor.fetchall()
        except sqlite3.Error as error:
            print(error)
        finally:
            cursor.close()
            connection.close()

    def select_info_about_user(self, user_id: int):
        """Метод для взятия данных пользователя из БД таблицы "user".\n
        Запрашивает только 1 аргумент: id - id пользователя в тг.\n
        Возвращает 1 значение: объект класса User
        :param user_id: telegram id пользователя
        :return: объект класса User
        """

        # Подключение к БД и создание курсора
        connection = sqlite3.connect(self.filename)
        cursor = connection.cursor()
        user_info = User(telegram_id=user_id)
        try:
            # Запрашивает все записи в БД таблице "user" у которого id
            cursor.execute('SELECT * FROM users WHERE tg_user_id = %s' % user_id)
            data = cursor.fetchone()
            # Если запись есть - объект класса User заполняется данными, полученными из БД
            if data != None and data != []:
                user_info = User(telegram_id=user_id,
                                 name=data[1],
                                 lastname=data[2],
                                 exam_type=data[3],
                                 if_get_course=data[4],
                                 total_ex=data[5],
                                 correct_ex=data[6],
                                 total_tests=data[7],
                                 total_points=data[8],
                                 most_points=data[9]
                                 )
        except sqlite3.Error as error:
            print(error)
        finally:
            cursor.close()
            connection.close()

        return user_info

    def select_info_about_users(self):
        '''
        Метод для взятия всех данных пользователя из БД таблицы "user"\n
        :return: двумерный массив с данными БД
        '''

        global data
        connection = sqlite3.connect(self.filename)
        cursor = connection.cursor()
        try:
            cursor.execute('SELECT * FROM users')  # Запрашивает все записи в БД таблице "user"
            data = list(
                map(list, cursor.fetchall()))  # Записывает эти данные в виде двумерного массива в переменную data

        except sqlite3.Error as error:
            print(error)
        finally:
            cursor.close()
            connection.close()
        return data


class Exercise:
    def __init__(self, ex_id: int = 0, file_id: str = None,
                 exam_type: str = None, number_of_ex_in_test: int = 0, right_answer: str = None,
                 total_attempts=0, right_attempts=0):
        '''
        :param ex_id: id файла в БД
        :param file_id: id файла на сервере ТГ
        :param exam_type: ПРОФИЛЬ|БАЗА|ОГЭ - тип экзамена
        :param number_of_ex_in_test: номер задания в тесте
        :param right_answer: Правильный ответ
        :param total_attempts: Сколько всего людей попробовало (Достаётся из БД, изначально 0)
        :param right_attempts: Сколько всего людей решило верно (Достаётся из БД, изначально 0)
        '''
        self.ex_id = ex_id
        self.file_id = file_id
        self.exam_type = exam_type
        self.number_of_ex_in_test = number_of_ex_in_test
        self.right_answer = right_answer
        self.total_attempts = total_attempts
        self.right_attempts = right_attempts


class Test:
    def __init__(self, test_id: int = None, file_id: str = None,
                 exam_type: str = None, right_answers: str = None, total_attempts: int = 0):
        """
        :param test_id: id файла в БД
        :param file_id: id файла на сервере ТГ
        :param exam_type: ПРОФИЛЬ|БАЗА|ОГЭ - тип экзамена
        :param right_answers: Правильный ответ
        :param total_attempts: сколько всего людей попробовало (Достаётся из БД, изначально 0)
        """
        self.test_id = test_id
        self.file_id = file_id
        self.right_answers = right_answers
        self.exam_type = exam_type
        self.total_attempts = total_attempts
        if exam_type == 'ПРОФИЛЬ':
            self.most_points = 3


load_dotenv()
bot = telebot.TeleBot(os.getenv('TOKEN'))

# Надо добить эту проверку на админов (bool)
if_admin = lambda message: str(message.chat.id) in os.getenv('ADMINS').split(sep=',')

# Создание объектов классов DB, User
db = DB('data.db')
user = User()
exercise = Exercise()
test = Test()


def on_starting():
    '''Уведомляет админов, что бот начал работу'''
    bot.send_message(chat_id=306383679, text='БОТ ЗАПУЩЕН /start')


# Обработчик при команде '/start'
@bot.message_handler(commands=['start'])
def start(message: types.Message):
    '''Стартовый обработчик'''

    # Создание клавиатуры
    kb = types.InlineKeyboardMarkup()

    # Создание объекта класса User
    global user
    user = db.select_info_about_user(message.from_user.id)

    # Если новый пользователь
    if not if_admin(message) and user.name is None:
        # Создание кнопок и добавление в клавиатуру
        btn1 = types.InlineKeyboardButton(text='Подписаться', url='https://t.me/dushnilamath')
        btn2 = types.InlineKeyboardButton(text='Регистрация', callback_data='registration')
        kb.add(btn1, btn2)
        # Отправка сообщения
        bot.send_message(message.chat.id,
                         text='''Привет, я тот самый бот душнила, помогу тебе сдать экзамен на максимум!
                                      \n Давай подпишемся на канал неДУШНАЯ математика и продолжим регистрацию''',
                         reply_markup=kb)
    # Если уже зарегистрирован или админ
    else:
        if if_admin(message):
            teacher_menu(message)
        else:
            student_menu(message)


@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback: types.CallbackQuery):
    """Обработка callback-запросов"""

    # Очистка контекста, чтобы бот не регистрировал новые сообщения от пользователя, когда они не нужны.
    bot.clear_step_handler_by_chat_id(chat_id=callback.message.chat.id)

    # Обработка callback-запросов для админов
    if if_admin(callback.message):
        # Меню добавления упражнения
        if callback.data == 'new exercise':
            add_exercise_type(callback.message)

        # Меню проверки упражнений
        elif callback.data == 'check exercises':
            no_function(callback)

        # Меню добавления варианта
        elif callback.data == 'new test':
            add_test_type(callback.message)

        # Меню проверки варианта
        elif callback.data == 'check test':
            no_function(callback)

        # Меню добавления домашнего задания
        elif callback.data == 'new homework':
            no_function(callback)

        # Меню проверки ДЗ
        elif callback.data == 'check homework':
            no_function(callback)

        # Меню статистики учеников
        elif callback.data == 'students` statistic':
            students_statistic(callback.message)

        elif callback.data == 'menu':
            teacher_menu(callback.message)

    # Обработчик запросов от нажатий кнопок обычных учеников
    else:
        # Регистрация
        if callback.data == 'registration':
            # Проверка подписки на основной канал
            try:
                if_member = bot.get_chat_member(chat_id='@dushnilamath', user_id=callback.message.chat.id)
                start_registration(callback.message)
            except Exception as error:  # Если не подписан, регистрация не начинается
                kb = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton(text='Подписаться', url='https://t.me/dushnilamath')
                btn2 = types.InlineKeyboardButton(text='Регистрация', callback_data='registration')
                kb.add(btn1, btn2)
                try:
                    bot.edit_message_text(f'Подпишись пж {error}',
                                          callback.message.chat.id,
                                          callback.message.message_id,
                                          reply_markup=kb)
                except Exception as e:
                    print(e)

        # Меню
        elif callback.data == 'menu':
            student_menu(callback.message)

        # Профиль пользователя
        elif callback.data == 'profile':
            profile(callback.message)

        # Меню заданий
        elif callback.data == 'do exercises':
            do_exercises_select_number(callback.message)

        # Меню тестов
        elif callback.data == 'do test':
            do_test_send_test(callback.message)

        elif callback.data == 'submit answers 1 part':
            check_answers_get_1_part(callback.message)

        elif callback.data == 'submit answers 2 part':
            no_function(callback)

        # Меню дз
        elif callback.data == 'homework':
            no_function(callback)

        # Меню обратиться преподу
        elif callback.data == 'chat with teacher':
            message_to_teacher(callback.message)

        # Меню с теорией
        elif callback.data == 'theory':
            no_function(callback)

        # Меню "Обратиться в техподдержку"
        elif callback.data == 'SOS':
            sos(callback.message)


"""Часть для учителя и админов"""


# Меню для учителя
def teacher_menu(message: types.Message):
    kb = types.InlineKeyboardMarkup()
    # Создание кнопок
    btn1 = types.InlineKeyboardButton('Добавить задания', callback_data='new exercise')
    btn2 = types.InlineKeyboardButton('Проверить задания', callback_data='check exercises')
    btn3 = types.InlineKeyboardButton('Добавить вариант', callback_data='new test')
    btn4 = types.InlineKeyboardButton('Проверить вариант', callback_data='check test')
    btn5 = types.InlineKeyboardButton('Добавить дз', callback_data='new homework')
    btn6 = types.InlineKeyboardButton('Проверить дз', callback_data='check homework')
    btn7 = types.InlineKeyboardButton('Статистика учеников', callback_data='students` statistic')
    # Добавление кнопок в клавиатуру
    kb.add(btn7)
    kb.row(btn1, btn2)
    kb.row(btn3, btn4)
    kb.row(btn5, btn6)

    # Вывод меню
    try:
        bot.edit_message_text(f'Что сделаем?',
                              chat_id=message.chat.id,
                              message_id=message.message_id,
                              reply_markup=kb)
    except:
        bot.send_message(message.chat.id, f'Что сделаем?', reply_markup=kb)
    # Финиш


# Добавление задач в банк
def add_exercise_type(message: types.Message):
    try:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('ПРОФИЛЬ')
        btn2 = types.KeyboardButton('БАЗА')
        btn3 = types.KeyboardButton('ОГЭ')
        kb.add(btn1, btn2, btn3)
        sent = bot.send_message(message.chat.id, 'Задача для какого экзамена?', reply_markup=kb)
        bot.register_next_step_handler(sent, add_exercise_answer)
    except:
        pass


def add_exercise_answer(message: types.Message):
    global exercise
    exercise.exam_type = message.text
    sent = bot.send_message(message.chat.id, 'Какой ответ на задачу?', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(sent, add_exercise_number_in_test)


def add_exercise_number_in_test(message: types.Message):
    global exercise
    exercise.right_answer = message.text
    sent = bot.send_message(message.chat.id, 'Какому номеру в тесте соответствует это задание')
    bot.register_next_step_handler(sent, add_exercise_ph)


def add_exercise_ph(message: types.Message):
    global exercise
    exercise.number_of_ex_in_test = message.text
    sent = bot.send_message(message.chat.id, 'Пришлите фотографию')
    bot.register_next_step_handler(sent, add_exercise_finish)


def add_exercise_finish(message: types.Message):
    global exercise
    try:
        exercise.file_id = message.photo[0].file_id
        db.add_info(
            '''INSERT INTO exercises(ex_file_id, exam_type, right_answer, number_of_ex_in_test) VALUES (?,?,?,?)''',
            [exercise.file_id, exercise.exam_type, exercise.right_answer, exercise.number_of_ex_in_test])
        kb = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
        btn2 = types.InlineKeyboardButton('Добавить задание', callback_data='new exercise')
        kb.add(btn1, btn2)
        bot.send_photo(message.chat.id, exercise.file_id,
                       f'УСПЕШНО ДОБАВЛЕНО \nЭкзамен: {exercise.exam_type} \nОтвет: {exercise.right_answer}',
                       reply_markup=kb)
    except:
        sent = bot.send_message(message.chat.id, 'Отправьте фотографию пж')
        bot.register_next_step_handler(sent, add_exercise_finish)
    # Финиш


# Добавление варианта в Банк
def add_test_type(message: types.Message):
    try:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('ПРОФИЛЬ')
        btn2 = types.KeyboardButton('БАЗА')
        btn3 = types.KeyboardButton('ОГЭ')
        kb.add(btn1, btn2, btn3)
        sent = bot.send_message(message.chat.id, 'Вариант какого экзамена?', reply_markup=kb)
        bot.register_next_step_handler(sent, add_test_answers)
    except Exception as error:
        print(error)


def add_test_answers(message: types.Message):
    global test
    test.exam_type = message.text
    sent = bot.send_message(message.chat.id, 'Отправьте ответы на 1 часть с пробелом как разделителем',
                            reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(sent, add_test_file)


def add_test_file(message: types.Message):
    global test
    test.right_answers = message.text
    sent = bot.send_message(message.chat.id, 'Пришлите файл')
    bot.register_next_step_handler(sent, add_test_finish)


def add_test_finish(message: types.Message):
    global test
    answers = test.right_answers.split()
    print(message)
    try:
        test.file_id = message.document.file_id
        db.add_info('''INSERT INTO tests(test_file_id, exam_type, right_answers) VALUES (?,?,?)''',
                    [test.file_id, test.exam_type, test.right_answers])
        test.test_id = db.select_info('''SELECT test_id FROM tests WHERE test_file_id = ?''', (test.file_id,))
        kb = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
        btn2 = types.InlineKeyboardButton('Добавить вариант', callback_data='new test')
        kb.add(btn1, btn2)
        bot.send_document(chat_id=message.chat.id, document=test.file_id,
                          caption=f'Успешно добавлено\n'
                                  f'Экзамен:{test.exam_type}\n'
                                  f'Вариант N:{test.test_id[0]}\n'
                                  f'Ответы первой части:\n' + '\n'.join(
                              [f'{i + 1}. {answers[i]}' for i in range(len(answers))]),
                          reply_markup=kb,
                          visible_file_name=f'Вариант номер {test.test_id} по {test.exam_type}')
    except Exception as error:
        print(error)
        sent = bot.send_message(message.chat.id, 'Ошибка. Отправьте файл пж')
        bot.register_next_step_handler(sent, add_test_finish)


# Отправка статистики по всем ученикам в виде excel таблицы
def students_statistic(message: types.Message):
    users = db.select_info_about_users()
    make_excel(users)
    file = open('statistic.xlsx', 'rb')
    bot.send_document(message.chat.id, file, visible_file_name='Файл со всей статистикой учеников.xlsx')
    # Финиш


"""Часть для учеников"""


# РЕГИСТРАЦИЯ
def start_registration(message: types.Message):  # Регистрация имени и фамилии
    sent = bot.send_message(message.chat.id, 'Напиши своё Имя и Фамилию')
    bot.register_next_step_handler(sent, select_course)


def select_course(message: types.Message):  # Регистрация курса
    global user
    try:
        user.name, user.lastname = message.text.split()
    except:
        user.name = message.text
        user.lastname = '...'

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton(text='ОГЭ')
    btn2 = types.KeyboardButton(text='ПРОФИЛЬ')
    btn3 = types.KeyboardButton(text='БАЗА')
    kb.add(btn1, btn2, btn3)
    sent = bot.send_message(message.chat.id, 'Что сдаёшь?', reply_markup=kb)
    bot.register_next_step_handler(sent, finish_registration)


def finish_registration(
        message: types.Message):  # Проверка в группах учеников: 0 - нигде нет, 1 - душный курс, 2 - недушный курс
    global user
    user.exam_type = message.text

    try:
        a = bot.get_chat_member(chat_id=-925122238, user_id=user.telegram_id)
        user.if_get_course = 1
    except:
        user.if_get_course = 0
    finally:
        db.add_info('INSERT INTO users(tg_user_id, name, lastname, exam_type, if_get_course) VALUES (?,?,?,?,?)',
                    [user.telegram_id, user.name, user.lastname, user.exam_type, user.if_get_course])

        bot.send_message(message.chat.id,
                         text='Поздравляю, регистрация пройдена успешно! \nУспешного обучения и высоких баллов',
                         reply_markup=types.ReplyKeyboardRemove())

    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text='В меню', callback_data='menu')
    kb.add(btn1)
    bot.send_message(message.chat.id,
                     text='Перейдём в меню?',
                     reply_markup=kb)
    # Окончание регистрации
    # Финиш


# Меню для учеников
def student_menu(message: types.Message):
    # Создание объекта класса User с данными из БД по первичному ключу - telegram id
    user = db.select_info_about_user(message.chat.id)

    # Создание клавиатуры
    kb = types.InlineKeyboardMarkup(row_width=1)

    # Меню для пользователей
    # Создание кнопок
    btn1 = types.InlineKeyboardButton('Профиль', callback_data='profile')
    btn2 = types.InlineKeyboardButton('Порешать задания', callback_data='do exercises')
    btn3 = types.InlineKeyboardButton('Решить вариант', callback_data='do test')
    kb.add(btn1)
    kb.row(btn2, btn3)
    # Дополнительные функции ученикам Душный и недушный курсов
    if user.if_get_course > 0:
        btn4 = types.InlineKeyboardButton('ДЗ', callback_data='homework')
        btn5 = types.InlineKeyboardButton('Написать преподу', callback_data='chat with teacher')
        btn7 = types.InlineKeyboardButton('Вся теория', callback_data='theory')
        kb.add(btn4, btn5, btn7)
    # Ученикам без курса предлагается его купить
    else:
        btn4 = types.InlineKeyboardButton('Купить курс', url='https://clck.ru/355ikC')
        kb.add(btn4)
    btn6 = types.InlineKeyboardButton('Написать в техподдержку', callback_data='SOS')
    kb.add(btn6)
    # Вывод меню
    try:
        bot.edit_message_text(f'Что сделаем, {user.name}?',
                              chat_id=message.chat.id,
                              message_id=message.message_id,
                              reply_markup=kb)
    except:
        bot.send_message(message.chat.id, f'Что сделаем, {user.name}?', reply_markup=kb)
    # Финиш


# Вывод профиля пользователя
def profile(message: types.Message):
    # Создание объекта класса User
    user = db.select_info_about_user(message.chat.id)

    # Создание клавиатуры
    kb = types.InlineKeyboardMarkup()

    # Создание кнопок
    btn1 = types.InlineKeyboardButton('Купить курс', url='https://clck.ru/355ikC')
    btn2 = types.InlineKeyboardButton('В меню', callback_data='menu')

    # Текст со статистикой ученика для сообщения
    text_for_bot = f'''
    Пользователь N: {user.telegram_id}
    \nИмя: {user.name}
    \nСтатистика решённых заданий: 
    \n\t{(user.correct_ex / user.total_ex) * 100 if user.total_ex != 0 else 0} % ({user.correct_ex} из {user.total_ex})
    \nСтатистика вариантов: 
    \n\tВ среднем {(user.total_points / (user.total_tests * 100)) * 100 if user.total_tests != 0 else 0} за тест
    \n\tНаибольший бал за вариант - {user.most_points}
    \n\tВсего решено {user.total_tests} варианта'''

    # Дополнение к тексту для тех, кто не купил курс
    if user.if_get_course == 0:
        text_for_bot += '\n\nХочешь улучшить свой бал? Записывайся на курс'
        kb.add(btn1)
    kb.add(btn2)

    # Вывод профиля ученика
    bot.edit_message_text(text=text_for_bot,
                          chat_id=message.chat.id,
                          message_id=message.message_id,
                          reply_markup=kb)
    # Финиш


# Решить задания
def do_exercises_select_number(message: types.Message):
    # Создание объекта класса User
    user = db.select_info_about_user(message.chat.id)

    sent = bot.send_message(message.chat.id,
                            f'Экзамен: {user.exam_type}\nКакой номер задания хочешь поботать? Пришли номер задания')
    bot.register_next_step_handler(sent, do_exercises_get_ex)


def do_exercises_get_ex(message: types.Message):
    global exercise
    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text='В меню', callback_data='menu')
    btn2 = types.InlineKeyboardButton(text='Ещё', callback_data='do exercises')
    kb.add(btn1, btn2)
    # Создание объекта класса User
    user = db.select_info_about_user(message.chat.id)
    exercise.number_of_ex_in_test = message.text
    try:
        ex_list = db.select_info(
            f'SELECT * FROM exercises WHERE exam_type = ? AND number_of_ex_in_test = ?',
            [user.exam_type, exercise.number_of_ex_in_test])
        random.shuffle(ex_list)
        i = random.randint(0, len(ex_list) - 1)
        exercise.file_id = ex_list[i][1]
        exercise.exam_type = ex_list[i][2]
        exercise.right_answer = ex_list[i][4]

        bot.send_photo(chat_id=message.chat.id, photo=exercise.file_id,
                       caption=f'Ответ: <tg-spoiler>{exercise.right_answer}</tg-spoiler>', parse_mode='HTML',
                       reply_markup=kb)
    except Exception as error:
        print(error)
        bot.send_message(message.chat.id, 'Заданий этого типа у меня ещё нет')
    # Финиш


def do_test_send_test(message: types.Message):
    global test
    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text='В меню', callback_data='menu')
    btn2 = types.InlineKeyboardButton(text='Сдать ответы', callback_data='submit answers 1 part')
    kb.add(btn1, btn2)
    # Создание объекта класса User
    user = db.select_info_about_user(message.chat.id)
    exercise.number_of_ex_in_test = message.text
    try:
        test_list = db.select_info(
            f'SELECT max(test_id), * FROM tests WHERE exam_type = ?;',
            [user.exam_type])
        test.test_id = test_list[0][1]
        test.file_id = test_list[0][2]
        test.exam_type = test_list[0][3]
        test.right_answers = test_list[0][4]
        bot.send_document(chat_id=message.chat.id, document=test.file_id,
                          caption=f'Удачи!\n' +
                                  f'Экзамен:{test.exam_type}\n' +
                                  f'Вариант N:{test.test_id}\n',
                          visible_file_name=f'Вариант номер {test.test_id} по {test.exam_type}',
                          reply_markup=kb)
    except Exception as error:
        print(error)
        bot.send_message(message.chat.id, 'Вариантов ещё нет')


def check_answers_get_1_part(message: types.Message):
    text_to_send = '''Пришли ответы *1 сообщением*, используя пробел как разделитель, как в примере.
    Пример: сообщение *"12 -34 56 ..."* будет распознано так:
    1 задание - *12* 
    2 задание - *-34* 
    3 задание - *56* 
    и т.д.'''
    sent = bot.send_message(message.chat.id,
                            text=text_to_send, parse_mode='Markdown')
    bot.register_next_step_handler(sent, check_answers_send_1_part)


def check_answers_send_1_part(message: types.Message):
    global test
    try:
        user_answers = message.text.split()
        test_answers = test.right_answers.split()
        kb = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton(text='В меню', callback_data='menu')
        btn2 = types.InlineKeyboardButton(text='Сообщить об ошибке', callback_data='SOS')

        kb.add(btn1, btn2)

        user = db.select_info_about_user(message.chat.id)
        if user.if_get_course > 0:
            btn3 = types.InlineKeyboardButton(text='Сдать 2 часть', callback_data='submit answers 2 part')
            btn4 = types.InlineKeyboardButton(text='Написать учителю', callback_data='chat with teacher')
            kb.add(btn3, btn4)

        k = ['❌'] * len(test_answers)
        text = ''
        for i in range(len(test_answers)):
            try:
                if user_answers[i] == test_answers[i]:
                    k[i] = '✅'
            except:
                user_answers.append('-')
            text += f"{i}. {test_answers[i]} {user_answers[i]} {k[i]}\n"
        text += f"Верно решено {k.count('✅')}/{len(k)}"
        bot.send_message(message.chat.id,
                         text=f'''N Правильный ответ Твой ответ\n{text}''', reply_markup=kb)
    except Exception as error:
        print(error)
        sent = bot.send_message(message.chat.id,
                                text='''Произошла Ошибка. Пришли ответы как в примере ещё раз''')
        bot.register_next_step_handler(sent, check_answers_send_1_part)


# Функция "Написать в техподдержку"
def sos(message: types.Message):
    # Создание клавиатуры и добавление кнопки "В меню"
    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
    kb.add(btn1)

    sent = bot.edit_message_text(
        '''Что-то случилось? Опиши проблему максимально как можешь. Можешь также прикрепить фотографию
        <tg-spoiler>Техподдержка не помогает в решении задач и вариантов</tg-spoiler>''',
        chat_id=message.chat.id,
        message_id=message.message_id,
        parse_mode='HTML',
        reply_markup=kb)

    # Регистрирует ответ пользователя на сообщение sent и передает в метод "sos2"
    bot.register_next_step_handler(sent, sos2)


def sos2(message: types.Message):
    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
    kb.add(btn1)
    bot.send_message(chat_id=message.chat.id,
                     text='Спасибо за обращение постараемся ответить в максимально ближайшее время',
                     reply_markup=kb)
    kb = types.InlineKeyboardMarkup()
    btn2 = types.InlineKeyboardButton('Ответить', callback_data='answer')
    kb.add(btn2)
    bot.forward_message(chat_id=os.getenv('HELP_CHAT'),
                        from_chat_id=message.chat.id,
                        message_id=message.message_id)
    bot.send_message(chat_id=os.getenv('HELP_CHAT'),
                     text=f'Обращение от @{message.from_user.username} ({message.from_user.id})',
                     reply_markup=kb)
    # Финиш


def message_to_teacher(message: types.Message):
    """Функция написать учителю. Запрашивает сообщение"""
    # Создание клавиатуры и добавление кнопки "В меню"
    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
    kb.add(btn1)

    # Заменяет текст сообщения с меню (экономия места)
    sent = bot.edit_message_text(
        text='''Возникли трудности в решении задачи? Напиши сообщение Олегу, надеюсь он поможет.
        \nПостарайся максимально объяснить ситуацию + постарайся предложить свой путь решения 
        (Даже если тебе кажется, что это неверно)
        <tg-spoiler>А можешь просто похвалить за хорошую работу)</tg-spoiler>''',
        chat_id=message.chat.id,
        message_id=message.message_id,
        parse_mode='HTML',
        reply_markup=kb)

    # Регистрирует ответ пользователя на сообщение sent и передает в метод "message_to_teacher_2"
    bot.register_next_step_handler(sent, message_to_teacher_2)


def message_to_teacher_2(message: types.Message):
    """Отправляет сообщения и предлагает выйти в меню"""
    # Отправляет сообщение в чат ученика
    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
    kb.add(btn1)
    bot.send_message(chat_id=message.chat.id,
                     text='Спасибо за обращение, Олег постарается ответить в максимально ближайшее время',
                     reply_markup=kb)
    # Отправляет сообщение в чат для учителя
    kb = types.InlineKeyboardMarkup()
    btn2 = types.InlineKeyboardButton('Ответить', callback_data='answer')
    kb.add(btn2)
    bot.send_message(chat_id=os.getenv('TEACHER_CHAT'),
                     text=f'Обращение от @{message.from_user.username}',
                     reply_markup=kb)
    bot.forward_message(chat_id=os.getenv('teacher_chat'),
                        from_chat_id=message.chat.id,
                        message_id=message.message_id)
    # Финиш


@bot.message_handler(chat_types=['private'])
def echo(message: types.Message):
    """Эхо, если пользователь начнёт писать не вовремя"""
    bot.send_message(message.chat.id, 'Я вас не понимаю, попробуйте использовать кнопки, нажав /start')

def no_function(callback: types.CallbackQuery):
    """Функиця вызывается, если выбранная на кнопках функция ещё не доработана"""
    bot.answer_callback_query(callback_query_id=callback.id,
                              text='Эта функция ещё недоступна: она дорабатывается',
                              show_alert=True)

if __name__ == '__main__':
    on_starting()  # уведомляет о запуске бота
    bot.polling()
