import os
import random

import telebot
from dotenv import load_dotenv
from telebot import types

from making_excel_with_statistic import make_excel
from models import *

load_dotenv()
bot = telebot.TeleBot(os.getenv('TOKEN'))

# Надо добить эту проверку на админов (bool)
if_admin = lambda message: str(message.chat.id) in os.getenv('ADMINS').split(sep=',')



def on_starting():
    """Уведомляет админов, что бот начал работу"""
    bot.send_message(chat_id=306383679, text='БОТ ЗАПУЩЕН /start')


@bot.message_handler(chat_types=['group', 'supergroup', 'channel'])
def do_nothing(message: types.Message):
    """Игнорирует команды в группах и каналах"""
    pass


# Обработчик при команде '/start'
@bot.message_handler(commands=['start'])
def start(message: types.Message):
    """Стартовый обработчик"""

    # Создание клавиатуры
    kb = types.InlineKeyboardMarkup()

    # Создание объекта класса User
    user, created = User.get_or_create(user_id=message.chat.id, defaults={'user_id': message.chat.id})

    # Если новый пользователь
    if not if_admin(message) and not user.name:
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
    """Обработчик callback-запросов"""

    # Очистка контекста, чтобы бот не регистрировал новые сообщения от пользователя, когда они не нужны.
    bot.clear_step_handler_by_chat_id(chat_id=callback.message.chat.id)
    try:
        # Обработка callback-запросов для админов
        if if_admin(callback.message):
            # Меню добавления упражнения
            if callback.data == 'new exercise':
                add_exercise(callback.message)

            # Меню проверки упражнений
            elif callback.data == 'check exercises':
                no_function(callback)

            # Меню добавления варианта
            elif callback.data == 'new test':
                add_test(callback.message)

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

            # Меню для учителя
            elif callback.data == 'menu':
                teacher_menu(callback.message)

        # Обработчик запросов от нажатий кнопок обычных учеников
        else:
            # Создание объекта класса User с данными из БД по первичному ключу - user id
            with conn:
                user = User.get_or_none(User.user_id == callback.message.chat.id)
            if not user:
                bot.send_message(callback.message.chat.id, 'Ой, я тебя чуток забыл, айда познакомимся снова')
                start(callback.message)
            else:
                # Регистрация
                if callback.data == 'registration':
                    registration(callback.message)

                # Меню
                elif callback.data == 'menu':
                    student_menu(callback.message)

                # Профиль пользователя
                elif callback.data == 'profile':
                    profile(callback.message)

                # Меню заданий
                elif callback.data == 'do exercises':
                    exercise_menu(callback.message)

                # Меню тестов
                elif callback.data == "test":
                    test_menu(callback.message)

                # Меню дз
                elif callback.data == 'homework':
                    no_function(callback)

                # Меню обратиться преподу
                elif callback.data == 'chat with teacher':
                    message_to_teacher_menu(callback.message)

                # Меню с теорией
                elif callback.data == 'theory':
                    no_function(callback)

                # Меню "Обратиться в техподдержку"
                elif callback.data == 'SOS':
                    support_message_menu(callback.message)

    except Exception as e:
        print('Check_callback_data: ', e)
        no_function(callback)


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
        bot.edit_message_text('Что сделаем,Хозяин?',
                              chat_id=message.chat.id,
                              message_id=message.message_id,
                              reply_markup=kb)
    except Exception as e:
        print('teacher_menu',e)
        bot.send_message(message.chat.id, f'Что сделаем?', reply_markup=kb)
    # Финиш


# Добавление задачи в банк
def add_exercise(message: types.Message):
    exercise = Exercise()

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
        nonlocal exercise
        exercise.exam_type = message.text
        sent = bot.send_message(message.chat.id, 'Какой ответ на задачу?', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(sent, add_exercise_number_in_test)

    def add_exercise_number_in_test(message: types.Message):
        nonlocal exercise
        exercise.right_answer = message.text
        sent = bot.send_message(message.chat.id, 'Какому номеру в тесте соответствует это задание')
        bot.register_next_step_handler(sent, add_exercise_ph)

    def add_exercise_ph(message: types.Message):
        nonlocal exercise
        exercise.number_of_ex_in_test = message.text
        sent = bot.send_message(message.chat.id, 'Пришлите фотографию')
        bot.register_next_step_handler(sent, add_exercise_finish)

    def add_exercise_finish(message: types.Message):
        nonlocal exercise
        try:
            exercise.file_id = message.photo[0].file_id
            with conn:
                exercise.save()
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

    add_exercise_type(message)


# Добавление варианта в Банк
def add_test(message: types.Message):
    test = Test()

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
            print('add_test_type', error)

    def add_test_answers(message: types.Message):
        nonlocal test
        test.exam_type = message.text
        sent = bot.send_message(message.chat.id, 'Отправьте ответы на 1 часть с пробелом как разделителем',
                                reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(sent, add_test_file)

    def add_test_file(message: types.Message):
        nonlocal test
        test.answers_1part = message.text
        sent = bot.send_message(message.chat.id, 'Пришлите файл')
        bot.register_next_step_handler(sent, add_test_finish)

    def add_test_finish(message: types.Message):
        nonlocal test
        answers = test.answers_1part.split()
        try:
            test.file_id = message.document.file_id
            with conn:
                test.save()
            kb = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
            btn2 = types.InlineKeyboardButton('Добавить вариант', callback_data='new test')
            kb.add(btn1, btn2)
            bot.send_document(chat_id=message.chat.id, document=test.file_id,
                              caption=f'Успешно добавлено\n'
                                      f'Экзамен:{test.exam_type}\n'
                                      f'Вариант N:{test.test_id}\n'
                                      f'Ответы первой части:\n' + '\n'.join(
                                  [f'{i + 1}. {answers[i]}' for i in range(len(answers))]),
                              reply_markup=kb,
                              visible_file_name=f'Вариант номер {test.test_id} по {test.exam_type}')
        except Exception as error:
            print('add_test_finish', error)
            sent = bot.send_message(message.chat.id, 'Ошибка. Отправьте файл пж')
            bot.register_next_step_handler(sent, add_test_finish)

    add_test_type(message)


# Отправка статистики по всем ученикам в виде excel таблицы
def students_statistic(message: types.Message):
    make_excel()
    file = open('statistic.xlsx', 'rb')
    bot.send_document(message.chat.id, file, visible_file_name='Файл со всей статистикой учеников.xlsx')
    # Финиш


"""Часть для учеников"""


# РЕГИСТРАЦИЯ
def registration(message: types.Message):
    user = User(user_id=message.chat.id)

    def start_registration(message: types.Message):  # Регистрация имени и фамилии
        sent = bot.send_message(message.chat.id, 'Напиши своё Имя и Фамилию')
        bot.register_next_step_handler(sent, select_course)

    def select_course(message: types.Message):  # Регистрация курса
        nonlocal user
        try:
            user.name, user.lastname = message.text.split()
        except:
            user.name = message.text
            user.lastname = '-'
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn1 = types.KeyboardButton(text='ОГЭ')
        btn2 = types.KeyboardButton(text='ПРОФИЛЬ')
        btn3 = types.KeyboardButton(text='БАЗА')
        kb.add(btn1, btn2, btn3)
        sent = bot.send_message(message.chat.id, 'Что сдаёшь?', reply_markup=kb)
        bot.register_next_step_handler(sent, finish_registration)

    def finish_registration(message: types.Message):
        # Проверка в группах учеников: 0 - нигде нет, 1 - душный курс, 2 - недушный курс
        nonlocal user
        user.exam_type = message.text
        try:
            a = bot.get_chat_member(chat_id=-925122238, user_id=user.user_id)
            user.if_get_course = 1
        except:
            user.if_get_course = 0
        finally:
            with conn:
                user.save()

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
            # Проверка подписки на основной канал

    # Проверка подписки на основной канал
    try:
        if_member = bot.get_chat_member(chat_id='@dushnilamath', user_id=message.chat.id)
        if if_member.status != 'member':
            raise Exception
        start_registration(message)
    except Exception as error:  # Если не подписан, регистрация не начинается
        kb = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(text='Подписаться', url='https://t.me/dushnilamath')
        btn2 = types.InlineKeyboardButton(text='Регистрация', callback_data='registration')
        kb.add(btn1, btn2)
        try:
            bot.edit_message_text(f'Подпишись пж {error}',
                                  message.chat.id,
                                  message.message_id,
                                  reply_markup=kb)
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
    btn1 = types.InlineKeyboardButton('Профиль', callback_data='profile')
    btn2 = types.InlineKeyboardButton('Порешать задания', callback_data='do exercises')
    btn3 = types.InlineKeyboardButton('Решить вариант', callback_data='test')
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
    # Создание объекта класса User с данными из БД по первичному ключу - user id
    with conn:
        user = User.get(User.user_id == message.chat.id)

    # Создание клавиатуры
    kb = types.InlineKeyboardMarkup()

    # Создание кнопок
    btn1 = types.InlineKeyboardButton('Купить курс', url='https://clck.ru/355ikC')
    btn2 = types.InlineKeyboardButton('В меню', callback_data='menu')

    # Текст со статистикой ученика для сообщения
    text_for_bot = f'''
    Пользователь N: {user.user_id}
    \nИмя: {user.name}
    \nСтатистика решённых заданий: 
    \n\t{(user.correct_ex / user.total_ex) * 100 if user.total_ex != 0 else 0} % ({user.correct_ex} из {user.total_ex})
    \nСтатистика вариантов: 
    \n\tВ среднем {(user.total_points / (user.total_tests * 100)) * 100 if user.total_tests != 0 else 0} за тест
    \n\tНаибольший бал за вариант - {user.max_points_per_test}
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
def exercise_menu(message: types.Message):
    # Создание объекта класса User с данными из БД по первичному ключу - user id
    with conn:
        user = User.get(User.user_id == message.chat.id)

    def select_number(message: types.Message):
        nonlocal user
        sent = bot.send_message(message.chat.id,
                                f'Экзамен: {user.exam_type}\nКакой номер задания хочешь поботать? Пришли номер задания')
        bot.register_next_step_handler(sent, get_ex)

    def get_ex(message: types.Message):
        nonlocal user
        kb = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(text='В меню', callback_data='menu')
        btn2 = types.InlineKeyboardButton(text='Ещё', callback_data='do exercises')
        kb.add(btn1, btn2)
        try:
            ex_type = message.text
            with conn:
                ex_list = [i for i in Exercise.select().where(Exercise.exam_type == user.exam_type,
                                                              Exercise.number_of_ex_in_test == ex_type)]

            random.shuffle(ex_list)
            exercise = random.choice(ex_list)
            bot.send_photo(chat_id=message.chat.id, photo=exercise.file_id,
                           caption=f'Ответ: <tg-spoiler>{exercise.right_answer}</tg-spoiler>', parse_mode='HTML',
                           reply_markup=kb)
        except Exception as error:
            print(error)
            bot.send_message(message.chat.id, 'Заданий этого типа у меня ещё нет')
        # Финиш

    select_number(message)


def test_menu(message: types.Message):
    """Главное меню для вариантов"""
    # Проверка наличия вариантов
    try:
        with conn:
            user = User.get(User.user_id == message.chat.id)
            test = [i for i in Test.select().where(Test.exam_type == user.exam_type).
                order_by(Test.test_id.desc()).execute()][0]
            user_test, created = UserTestResult.get_or_create(test_id=test.test_id,
                                                              defaults={'test_id': test.test_id,
                                                                        'user_id': user.user_id,
                                                                        'exam_type': user.exam_type})


        def submit_1part_answers(message: types.Message):
            try:
                text = '''Пришли ответы *1 сообщением*, используя пробел как разделитель, как в примере.
                Пример: сообщение *"12 -34 56 ..."* будет распознано так:
                1 задание - *12* 
                2 задание - *-34* 
                3 задание - *56* 
                и т.д.'''
                sent = bot.send_message(chat_id=message.chat.id,
                                        text=text,
                                        parse_mode='Markdown')
                bot.register_next_step_handler(sent, save_1part)
            except Exception as e:
                print('submit_1part_answers', e)

        def save_1part(message: types.Message):
            nonlocal user_test, test, user
            try:# Получение ответов от пользователя
                user_answers = message.text.split()  # конвертация строки с ответами пользователя-> список
                test_answers = test.answers_1part.split()  # Получение правильных ответов из БД
                map(int, user_answers)  # проверка на числовое значение
                # Алгоритм сверяет ответы
                k = ['❌'] * len(test_answers)
                for i in range(len(test_answers)):
                    try:
                        if user_answers[i] == test_answers[i]:
                            k[i] = '✅'  # Отмечается правильным, если элементы совпадают
                    except:
                        user_answers.append('-')  # Если ученик сдал не все ответы,
                    # Сохранение результатов
                    user_test.answers_1part = ' '.join(user_answers)  # Сохранение строки с ответами в БД
                    user_test.result_1part = ' '.join(k)  # Сохранение строки с результатом проверки в БД
                    user_test.points_of_1_part = k.count('✅') # Сохранение количества набранных баллов за 1 часть

                submit_2part_answers(message) #
            except:
                sent = bot.send_message(chat_id=message.chat.id,
                                        text='Произошла Ошибка. Пришли ответы как в примере ещё раз')
                bot.register_next_step_handler(sent, submit_1part_answers)

        def submit_2part_answers(message: types.Message):
            """Поучение от пользователя фотографий с его решением 2 части"""
            nonlocal user, test, user_test
            kb = types.InlineKeyboardMarkup()

            if user.if_get_course == '0':
                user_test.student_file_id = None
                btn1 = types.InlineKeyboardButton('Перейти к результатам', callback_data='test')
                btn2 = types.InlineKeyboardButton('Купить курс', url='https://clck.ru/355ikC')
                kb.add(btn1, btn2)
                bot.send_message(chat_id=message.chat.id,
                                 text='Для экспертной проверки 2 части нужно купить курс',
                                 reply_markup=kb)

            else:
                sent = bot.send_message(chat_id=message.chat.id,
                                        text='''Пришли следующим сообщением фотографии решения 2 части. 
                Важно прислать их 1 сообщением, а не по отдельности, чтобы я правильно их принял''')
                bot.register_next_step_handler(sent, save_2part)

        def save_2part(message: types.Message):
            nonlocal user, test, user_test
            try:
                user_test.student_file_id = ' '.join([ph.file_id for ph in message.photo])
                with conn:
                    user_test.save()
                    test.total_attempts+=1
                    test.save()
                send_results()
            except Exception as e:
                print('save_2part',e)
                sent = bot.send_message(message.chat.id, 'Отправь фотки, а не файлы')
                bot.register_next_step_handler(sent, save_2part)


        def send_results(message: types.Message):
            nonlocal user, test, user_test
            test_answers = test.answers_1part.split()
            user_answers = user_test.answers_1part.split()
            user_results_1part = user_test.result_1part.split()
            user_points = user_test.points_of_1_part
            text = 'Результаты 1 части\nN Правильный ответ Твой ответ\n'
            text+= '\n'.join([f"{i+1}. {test_answers[i]} {user_answers[i]} {user_results_1part[i]}" for i in range(len(test_answers))])
            bot.send_message(message.chat.id,
                             text=text)
            kb = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
            kb.add(btn1)
            if user_test.teacher_file_id:
                bot.send_document(chat_id=message.chat.id,
                                  document=user_test.teacher_file_id,
                                  caption=f'Результат проверки 2 части: {user_test.points_of_2_part} баллов',
                                  visible_file_name=f'{user.name} 2 часть {test.test_id}',
                                  reply_markup=kb)
            else:
                bot.send_message(message.chat.id,
                                 text='2 часть не проверена', reply_markup=kb)

        # Создание клавиатуры
        kb = types.InlineKeyboardMarkup()
        if created:
            # Если новый вариант ещё не отправлен
            btn1 = types.InlineKeyboardButton(text='В меню', callback_data='menu')
            kb.add(btn1)
            bot.send_document(chat_id=message.chat.id, document=test.file_id,
                              caption=f'Удачи!\n' +
                                      f'Экзамен:{test.exam_type}\n' +
                                      f'Вариант N:{test.test_id}\n',
                              visible_file_name=f'Вариант номер {test.test_id} по {test.exam_type}',
                              reply_markup=kb)
            with conn:
                user.last_test_id = test.test_id
        else:
            # Если новый вариант уже отправлен
            if user_test.answers_1part:  # Если ответы на 1 часть уже сданы

                bot.send_message(chat_id=message.chat.id,
                                 text="Результаты уже есть, сейчас отправлю")
                send_results(message)
            else:  # Если ответы ещё не сданы
                bot.send_message(chat_id=message.chat.id,
                                 text="Для получения результатов сдайте ответы")
                submit_1part_answers(message)
    except Exception as error:
        print('test_menu', error)
        bot.send_message(message.chat.id, 'Вариантов ещё нет')

def support_message_menu(message: types.Message):
    """Функция "Написать в техподдержку\""""

    def get_msg(message: types.Message):
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

        # Регистрирует ответ пользователя на сообщение sent и передает в метод "send_msg"
        bot.register_next_step_handler(sent, send_msg)

    def send_msg(message: types.Message):
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

    get_msg(message)


def message_to_teacher_menu(message: types.Message):
    """Функция написать учителю. Запрашивает сообщение"""

    def get_msg(message: types.Message):
        # Создание клавиатуры и добавление кнопки "В меню"
        kb = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('В меню', callback_data='menu')
        kb.add(btn1)

        # Заменяет текст сообщения с меню (экономия места)
        sent = bot.send_message(
            text=('Возникли трудности в решении задачи? Напиши сообщение Олегу, надеюсь он поможет.\n'
                  'Постарайся максимально объяснить ситуацию + постарайся предложить свой путь решения'
                  '(Даже если тебе кажется, что это неверно)\n'
                  '<tg-spoiler>А можешь просто похвалить за хорошую работу)</tg-spoiler>'),
            chat_id=message.chat.id,
            parse_mode='HTML',
            reply_markup=kb)

        # Регистрирует ответ пользователя на сообщение sent и передает в метод "message_to_teacher_2"
        bot.register_next_step_handler(sent, send_msg)

    def send_msg(message: types.Message):
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
        btn2 = types.InlineKeyboardButton('Ответить', callback_data='answer to student question')
        kb.add(btn2)
        bot.send_message(chat_id=os.getenv('TEACHER_CHAT'),
                         text=f'Обращение от @{message.from_user.username}',
                         reply_markup=kb)
        bot.forward_message(chat_id=os.getenv('teacher_chat'),
                            from_chat_id=message.chat.id,
                            message_id=message.message_id)

    get_msg(message)


def no_function(callback: types.CallbackQuery):
    """Функция вызывается, если выбранная на кнопках функция ещё не доработана"""
    bot.answer_callback_query(callback_query_id=callback.id,
                              text='Эта функция ещё недоступна: скорее всего она дорабатывается',
                              show_alert=True)


@bot.message_handler(chat_types=['private'])
def echo(message: types.Message):
    """Эхо, если пользователь начнёт писать не вовремя"""
    bot.send_message(message.chat.id, 'Я вас не понимаю, попробуйте использовать кнопки, нажав /start')


if __name__ == '__main__':
    # Создание таблицы и объектов таблиц (моделей)
    with conn:
        conn.create_tables([ExamType, User, Exercise, Test, UserTestResult, UserHomeworkResult])

        exams = [{'exam_type': 'ПРОФИЛЬ',
                  'number_of_questions': 18,
                  'max_points': 31,
                  'max_points_for_every_question': '1 1 1 1 1 1 1 1 1 1 1 2 3 2 2 3 4 4'},
                 {'exam_type': 'БАЗА',
                  'number_of_questions': 18,
                  'max_points': 21,
                  'max_points_for_every_question': '1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1'},
                 {'exam_type': 'ОГЭ',
                  'number_of_questions': 25,
                  'max_points': 31,
                  'max_points_for_every_question': '1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 2 2 2 2 2 2'}]
        try:
            ExamType.insert_many(exams).execute()
        except:
            pass
    # уведомляет о запуске бота
    on_starting()
    bot.polling()
