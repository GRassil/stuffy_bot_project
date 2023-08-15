import os
import random
import sqlite3

import telebot
from dotenv import load_dotenv
from telebot import types

from making_excel_with_statistic import make_excel


# Класс User - отвечает за данные пользователя
class User:
    def __init__(self, name=None, lastname=None, telegram_id=None, exam=None, if_get_course=0,
                 total_ex=0, correct_ex=0, total_tests=0, total_points=0, most_points=0):
        self.telegram_id = telegram_id  # id пользователя в тг
        self.name = name  # Имя пользователя
        self.lastname = lastname  # Фамилия пользователя
        self.exam = exam  # Экзамен, который он/она будет сдавать: ОГЭ/ЕГЭ база/ЕГЭ профиль
        self.if_get_course = if_get_course  # Купил ли пользователь курс: 0 - нет; 1 - душный курс; 2 - недушный курс
        # Далее данные, нужные для статистики
        self.total_ex = total_ex  # Сколько всего заданий пользователь решал
        self.correct_ex = correct_ex  # Сколько всего заданий пользователь решил верно
        self.total_tests = total_tests  # Сколько всего вариантов решил пользователь
        self.total_points = total_points  # Сколько суммарно набрал баллов
        self.most_points = most_points  # Наивысший бал, набранный пользователем за 1 вариант


# Класс DB отвечает за связь (обмен данными) с Базой Данных (далее БД)
class DB:
    # Инициализация класса
    def __init__(self, filename):
        self.filename = filename  # Имя файла с БД
        db = sqlite3.connect(self.filename)
        cursor = db.cursor()
        # Создание таблицы "users"
        cursor.execute('''CREATE TABLE IF NOT EXISTS users(
                            tg_user_id INTEGER PRIMARY KEY UNIQUE NOT NULL,
                            name TEXT,
                            lastname TEXT,
                            exam TEXT,
                            if_get_course INTEGER,
                            total_ex INTEGER DEFAULT (0),
                            correct_ex INTEGER DEFAULT (0),
                            total_tests INTEGER DEFAULT (0),
                            total_points INTEGER DEFAULT (0),
                            most_points INTEGER DEFAULT (0))''')

        # Создание таблицы "exercises"
        cursor.execute('''CREATE TABLE IF NOT EXISTS exercises(
                            ex_id auto_increment TEXT PRIMARY KEY NOT NULL UNIQUE,
                            exam_type TEXT NOT NULL,
                            number_of_ex_in_test INTEGER NOT NULL,                      
                            right_answer TEXT NOT NULL,
                            total_attempts INTEGER,
                            right_attempts INTEGER);''')

        # Надо ешё создать таблицы с ДЗ, Банком Вариантов и тд
        cursor.close()
        db.close()

    # Метод для добавления данных в БД.
    # Запрашивает 2 аргумента:
    # request - SQL запрос,
    # values - значения
    def add_info(self, request, values):
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

    # Общий метод для взятия данных с БД.
    # Запрашивает 1 аргумент:
    # request - SQL запрос
    def select_info(self, request, values):
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

    # Метод для взятия данных пользователя из БД таблицы "user".
    # Запрашивает только 1 аргумент: id - id пользователя в тг.
    # Возвращает 1 значение: объект класса User
    def select_info_about_user(self, user_id: int):
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
                                 exam=data[3],
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

    # Метод для взятия всех данных пользователя из БД таблицы "user"
    # Возвращает 1 значение: двумерный массив
    def select_info_about_users(self):
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
    def __init__(self, photo_id=None, right_answer=None, exam_type=None, number_of_ex_in_test=None,
                 total_attempts=0, right_attempts=0):
        self.photo_id = photo_id
        self.right_answer = right_answer
        self.exam_type = exam_type
        self.number_of_ex_in_test = number_of_ex_in_test
        self.total_attempts = total_attempts
        self.right_attempts = right_attempts


load_dotenv()
bot = telebot.TeleBot(os.getenv('TOKEN'))

# Надо добить эту проверку на админов (bool)
if_admin = lambda message: str(message.chat.id) in os.getenv('ADMINS').split(sep=',')

# Создание объектов классов DB, User
db = DB('data.db')
user = User()
exercise = Exercise()

def on_starting():
    bot.send_message(chat_id=int(os.getenv('HELP_CHAT')),text='БОТ ЗАПУЩЕН')

# Обработчик при команде '/start'
@bot.message_handler(commands=['start'])
def start(message):
    # Стартовый обработчик
    # Создание клавиатуры
    kb = types.InlineKeyboardMarkup()

    # Создание объекта класса User
    global user
    user = db.select_info_about_user(message.from_user.id)

    if user.name == None:
        # Создание кнопок и добавление в клавиатуру
        btn1 = types.InlineKeyboardButton(text='Подписаться', url='https://t.me/dushnilamath')
        btn2 = types.InlineKeyboardButton(text='Регистрация', callback_data='registration')
        kb.add(btn1, btn2)
        bot.send_message(message.chat.id,
                         text='''Привет, я тот самый бот душнила, помогу тебе сдать экзамен на максимум!
                                      \n Давай подпишемся на канал неДУШНАЯ математика и продолжим регистрацию''',
                         reply_markup=kb)
    else:
        if if_admin(message):
            teacher_menu(message)
        else:
            menu(message)


@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback):
    # Обработка callback-запросов для админов
    if if_admin(callback.message):
        # Меню добавления упражнения
        if callback.data == 'new exercise':
            add_exercise_type(callback.message)

        # Меню проверки упражнений
        elif callback.data == 'check exercises':
            pass

        # Меню добавления варианта
        elif callback.data == 'new test':
            pass

        # Меню проверки варианта
        elif callback.data == 'check test':
            pass

        # Меню добавления домашнего задания
        elif callback.data == 'new homework':
            pass

        # Меню проверки ДЗ
        elif callback.data == 'check homework':
            pass

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
                except:
                    pass

        # Меню
        elif callback.data == 'menu':
            menu(callback.message)

        # Профиль пользователя
        elif callback.data == 'profile':
            profile(callback.message)

        # Меню заданий
        elif callback.data == 'do exercises':
            do_exercises_select_number(callback.message)

        # Меню тестов
        elif callback.data == 'do test':
            pass

        # Меню дз
        elif callback.data == 'homework':
            pass

        # Меню обратиться преподу
        elif callback.data == 'chat with teacher':
            message_to_teacher(callback.message)

        # Меню с теорией
        elif callback.data == 'theory':
            pass

        # Меню "Обратиться в техподдержку"
        elif callback.data == 'SOS':
            sos(callback.message)


# СДЕЛААААТЬ
def add_exercise_type(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('ПРОФИЛЬ')
        btn2 = types.KeyboardButton('БАЗА')
        btn3 = types.KeyboardButton('ОГЭ')
        kb.add(btn1, btn2, btn3)
        sent = bot.send_message(message.chat.id, 'Задача для какого экзамена?', reply_markup=kb)
        bot.register_next_step_handler(sent, add_exercise_answer)
    except:
        pass


def add_exercise_answer(message):
    exercise.exam_type = message.text
    sent = bot.send_message(message.chat.id, 'Какой ответ на задачу?', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(sent, add_exercise_number_in_test)


def add_exercise_number_in_test(message):
    exercise.right_answer = message.text
    sent = bot.send_message(message.chat.id, 'Какому номеру в тесте соответствует это задание')
    bot.register_next_step_handler(sent, add_exercise_ph)


def add_exercise_ph(message):
    exercise.number_of_ex_in_test = message.text
    sent = bot.send_message(message.chat.id, 'Пришлите фотографию')
    bot.register_next_step_handler(sent, add_exercise_finish)


def add_exercise_finish(message):
    try:
        exercise.photo_id = message.photo[0].file_id
        db.add_info('''INSERT INTO exercises(ex_id, exam_type, right_answer, number_of_ex_in_test) VALUES (?,?,?,?)''',
                    (exercise.photo_id, exercise.exam_type, exercise.right_answer, exercise.number_of_ex_in_test))
        kb = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
        btn2 = types.InlineKeyboardButton('Добавить задание', callback_data='new exercise')
        kb.add(btn1, btn2)
        bot.send_photo(message.chat.id, exercise.photo_id,
                       f'УСПЕШНО ДОБАВЛЕНО \nЭкзамен: {exercise.exam_type} \nОтвет: {exercise.right_answer}',
                       reply_markup=kb)
    except:
        bot.delete_message(message.chat.id, message.id)
        bot.delete_message(message.chat.id, message.message_id - 1)
        sent = bot.send_message(message.chat.id, 'Отправьте фотографию пж')
        bot.register_next_step_handler(sent, add_exercise_finish)


# Отправка статистики по всем ученикам в виде excel таблицы
def students_statistic(message):
    users = db.select_info_about_users()
    make_excel(users)
    file = open('statistic.xlsx', 'rb')
    bot.send_document(message.chat.id, file, visible_file_name='Файл со всей статистикой учеников.xlsx')

    # Меню для учителя


def teacher_menu(message):
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


# РЕГИСТРАЦИЯ
def start_registration(message):  # Регистрация имени и фамилии
    sent = bot.send_message(message.chat.id, 'Напиши своё Имя и Фамилию')
    bot.register_next_step_handler(sent, select_course)


def select_course(message):  # Регистрация курса
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


def finish_registration(message):  # Проверка в группах учеников: 0 - нигде нет, 1 - душный курс, 2 - недушный курс
    global user
    user.exam = message.text

    try:
        if bot.get_chat_member(chat_id=-925122238, user_id=user.telegram_id):
            user.if_get_course = 1
    except:
        user.if_get_course = 0
    finally:
        db.add_info('INSERT INTO users(tg_user_id, name, lastname, exam, if_get_course) VALUES (?,?,?,?,?)',
                    (user.telegram_id, user.name, user.lastname, user.exam, user.if_get_course))

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


# МЕНЮ для школьников
def menu(message):
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


# Вывод профиля пользователя
def profile(message):
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
        text_for_bot += '''\n\nХочешь улучшить свой бал? Записывайся на курс'''
        kb.add(btn1)
    kb.add(btn2)

    # Вывод профиля ученика
    bot.edit_message_text(text=text_for_bot,
                          chat_id=message.chat.id,
                          message_id=message.message_id,
                          reply_markup=kb)


# Решить задания
def do_exercises_select_number(message):
    # Создание объекта класса User
    user = db.select_info_about_user(message.chat.id)

    sent = bot.send_message(message.chat.id,
                            f'Экзамен: {user.exam}\nКакой номер задания хочешь поботать? Пришли номер задания')
    bot.register_next_step_handler(sent, do_exercises_get_ex)


def do_exercises_get_ex(message):
    global exercise
    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text='В меню', callback_data='menu')
    btn2 = types.InlineKeyboardButton(text='Ещё', callback_data='do exercises')
    kb.add(btn1,btn2)
    # Создание объекта класса User
    user = db.select_info_about_user(message.chat.id)
    exercise.number_of_ex_in_test=message.text
    try:
        ex_list = db.select_info(
            f'SELECT * FROM exercises WHERE exam_type = ? AND number_of_ex_in_test = ?',
            [user.exam, exercise.number_of_ex_in_test])
        print(ex_list)
        random.shuffle(ex_list)
        i = random.randint(0,len(ex_list)-1)
        print(i)
        exercise.photo_id = ex_list[i][0]
        exercise.exam_type = ex_list[i][1]
        exercise.right_answer = ex_list[i][3]

        bot.send_photo(chat_id=message.chat.id, photo=exercise.photo_id,
                       caption=f'Ответ: <tg-spoiler>{exercise.right_answer}</tg-spoiler>', parse_mode='HTML',reply_markup=kb)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, 'Заданий этого типа у меня ещё нет')


# Функция "Написать в техподдержку"
def sos(message):
    # Создание клавиатуры и добавление кнопки "В меню"
    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
    kb.add(btn1)

    sent = bot.edit_message_text(
        '''Что-то случилось? Опиши проблему максимально как можешь.
        <tg-spoiler> Мы не помогаем в решении задач и вариантов</tg-spoiler>''',
        chat_id=message.chat.id,
        message_id=message.message_id,
        parse_mode='HTML',
        reply_markup=kb)

    # Регистрирует ответ пользователя на сообщение sent и передает в метод "sos2"
    bot.register_next_step_handler(sent, sos2)


def sos2(message):
    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
    kb.add(btn1)
    bot.delete_message(chat_id=message.chat.id,
                       message_id=message.message_id - 1)
    bot.delete_message(chat_id=message.chat.id,
                       message_id=message.message_id)
    bot.send_message(chat_id=message.chat.id,
                     text='Спасибо за обращение постараемся ответить в максимально ближайшее время',
                     reply_markup=kb)
    bot.send_message(chat_id=os.getenv('HELP_CHAT'),
                     text=f'Обращение от @{message.from_user.username}:\n{message.text}')


def message_to_teacher(message):
    # Создание клавиатуры и добавление кнопки "В меню"
    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
    kb.add(btn1)

    sent = bot.edit_message_text(
        '''Возникли трудности в решении задачи? Напиши сообщение Олегу, надеюсь он поможет.
        \nПостарайся максимально объяснить ситуацию + постарайся предложить свой путь решения 
        (Даже если тебе кажется, что это неверно)
        <tg-spoiler>А можешь просто похвалить за хорошую работу)</tg-spoiler>''',
        chat_id=message.chat.id,
        message_id=message.message_id,
        parse_mode='HTML',
        reply_markup=kb)

    # Регистрирует ответ пользователя на сообщение sent и передает в метод "message_to_teacher_2"
    bot.register_next_step_handler(sent, message_to_teacher_2)


def message_to_teacher_2(message):
    kb = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
    kb.add(btn1)
    bot.delete_message(chat_id=message.chat.id,
                       message_id=message.message_id - 1)
    bot.delete_message(chat_id=message.chat.id,
                       message_id=message.message_id)
    bot.send_message(chat_id=message.chat.id,
                     text='Спасибо за обращение, Олег постарается ответить в максимально ближайшее время',
                     reply_markup=kb)
    bot.send_message(chat_id=os.getenv('TEACHER_CHAT'),
                     text=f'Обращение от @{message.from_user.username}:\n{message.text}')


# Эхо на всякий случай
@bot.message_handler(chat_types=['private'])
def echo(message):
    bot.send_message(message.chat.id, 'Я вас не понимаю, попробуйте использовать кнопки')
    bot.delete_message(message.chat.id, message.message_id)
    bot.delete_message(message.chat.id, message.message_id + 1)


if __name__ == '__main__':
    # Зацикливание бота
    on_starting()
    bot.polling()
