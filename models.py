from peewee import *
import os

# Создаем базу данных в текущей директории
db = SqliteDatabase('barbershop.db')

class BaseModel(Model):
    class Meta:
        database = db

class Master(BaseModel):
    first_name = CharField(max_length=50)
    last_name = CharField(max_length=50)
    middle_name = CharField(max_length=50, null=True)
    phone = CharField(max_length=20, unique=True)

class Appointment(BaseModel):
    client_name = CharField(max_length=100)
    client_phone = CharField(max_length=20)
    date = DateTimeField()
    status = CharField(max_length=20, default='ожидает')
    comment = TextField(null=True)
    master = ForeignKeyField(Master, backref='appointments')

def initialize_db():
    """Инициализация базы данных"""
    db.connect()
    db.create_tables([Master, Appointment], safe=True)
