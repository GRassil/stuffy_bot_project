# Импортируем библиотеку, соответствующую типу нашей базы данных
from peewee import *

# Создаем соединение с нашей базой данных
conn = SqliteDatabase('database.db')


"""ТУТ КОД НАШИХ МОДЕЛЕЙ"""

# Определяем базовую модель о которой будут наследоваться остальные
class BaseModel(Model):
    class Meta:
        database = conn  # соединение с базой, из шаблона выше


# Модель типа экзамена
class ExamType(BaseModel):
    exam_type = TextField(primary_key=True)
    number_of_questions = IntegerField()
    max_points = IntegerField()
    max_points_for_every_question = TextField()

# Модель пользователя
class User(BaseModel):
    user_id = IntegerField(primary_key=True)
    name = TextField(null=True, default=None)
    lastname = TextField(null=True, default=None)
    exam_type = ForeignKeyField(ExamType, null=True, column_name='exam_type')
    if_get_course = IntegerField(default=0, null=True)
    total_ex = IntegerField(default=0, null=True)
    correct_ex = IntegerField(default=0, null=True)
    total_tests = IntegerField(default=0, null=True)
    total_points = IntegerField(default=0, null=True)
    max_points_per_test = IntegerField(default=0, null=True)

# Модель упражнения
class Exercise(BaseModel):
    ex_id = AutoField(primary_key=True)
    file_id = TextField()
    exam_type = ForeignKeyField(ExamType, column_name='exam_type')
    number_of_ex_in_test = IntegerField(default=0)
    right_answer = TextField(null=True)
    total_attempts = IntegerField(default=0, null=True)
    right_attempts = IntegerField(default=0, null=True)

# Модель упражнения
class Homework1part(BaseModel):
    hw_id = AutoField(primary_key=True)
    file_id = TextField()
    exam_type = ForeignKeyField(ExamType, column_name='exam_type')
    right_answer = TextField(null=True)
    total_attempts = IntegerField(default=0, null=True)
    right_attempts = IntegerField(default=0, null=True)

# Модель упражнения
class Homework2part(BaseModel):
    hw_id = AutoField(primary_key=True)
    file_id = TextField()
    exam_type = ForeignKeyField(ExamType, column_name='exam_type')
    total_attempts = IntegerField(default=0, null=True)
    right_attempts = IntegerField(default=0, null=True)

# Модель варианта
class Test(BaseModel):
    test_id = AutoField(primary_key=True)
    file_id = TextField()
    exam_type = ForeignKeyField(ExamType, column_name='exam_type')
    answers_1part = TextField(null=True)
    total_attempts = IntegerField(default=0)

# Модель результатов решения варианта каждого пользователя
class UserTestResult(BaseModel):
    result_id = AutoField(primary_key=True)
    user_id = ForeignKeyField(User)
    test_id = ForeignKeyField(Test)
    exam_type = ForeignKeyField(ExamType, column_name='exam_type')
    answers_1part = TextField(null=True)
    result_1part = TextField(null=True)
    student_file_id = TextField(null=True)
    teacher_file_id = TextField(null=True)
    points_of_1_part = IntegerField(default=0)
    points_of_2_part = IntegerField(default=0)

# Модель домашних заданий каждого пользователя
class UserHomeworkResult(BaseModel):
    result_id = AutoField(primary_key=True)
    user_id = ForeignKeyField(User)
    hw_id = ForeignKeyField(Test)
    exam_type = ForeignKeyField(ExamType, column_name='exam_type')
    answers_1part = TextField(null=True)
    student_file_id = TextField(null=True)
    teacher_file_id = TextField(null=True)
    points_of_1_part = IntegerField(default=0)
    points_of_2_part = IntegerField(default=0)


if __name__ == '__main__':
    with  conn:
        conn.create_tables([ExamType, User, Exercise, Test, UserTestResult, UserHomeworkResult])
    # Не забываем закрыть соединение с базой данных
