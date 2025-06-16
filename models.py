from peewee import *
from datetime import datetime
import os
from playhouse.signals import post_save
from typing import List, Optional

db = SqliteDatabase('barbershop.db')

class BaseModel(Model):
    class Meta:
        database = db

class Service(BaseModel):
    title = CharField(max_length=100, unique=True, verbose_name='Название')
    description = TextField(null=True, verbose_name='Описание')
    price = DecimalField(max_digits=7, decimal_places=2, verbose_name='Цена')

    def __str__(self):
        return self.title

class Master(BaseModel):
    first_name = CharField(max_length=50, verbose_name='Имя')
    last_name = CharField(max_length=50, verbose_name='Фамилия')
    middle_name = CharField(max_length=50, null=True, verbose_name='Отчество')
    phone = CharField(max_length=20, unique=True, verbose_name='Телефон')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Appointment(BaseModel):
    client_name = CharField(max_length=100, verbose_name='Имя клиента')
    client_phone = CharField(max_length=20, verbose_name='Телефон клиента')
    date = DateTimeField(default=datetime.now, verbose_name='Дата записи')
    status = CharField(max_length=20, default='ожидает', verbose_name='Статус')
    comment = TextField(null=True, verbose_name='Комментарий')
    master = ForeignKeyField(Master, backref='appointments', verbose_name='Мастер')

    def validate(self):
        """Валидация данных записи."""
        if not self.client_name.strip():
            raise ValidationError("Имя клиента не может быть пустым")
        if not self.client_phone.strip():
            raise ValidationError("Телефон клиента не может быть пустым")
        if len(self.client_phone) < 5:
            raise ValidationError("Телефон слишком короткий")

    def __str__(self):
        return f"Запись #{self.id} для {self.client_name}"

class MasterService(BaseModel):
    master = ForeignKeyField(Master, verbose_name='Мастер')
    service = ForeignKeyField(Service, verbose_name='Услуга')

    class Meta:
        indexes = (
            (('master', 'service'), True),
        )

class AppointmentService(BaseModel):
    appointment = ForeignKeyField(Appointment, verbose_name='Запись')
    service = ForeignKeyField(Service, verbose_name='Услуга')

    class Meta:
        indexes = (
            (('appointment', 'service'), True),
        )

@post_save(sender=Appointment)
def validate_appointment(model_class, instance, created):
    try:
        instance.validate()
    except ValidationError as e:
        if created:
            instance.delete_instance()
        raise e

def initialize_db():
    """Инициализация базы данных"""
    db.connect()
    db.create_tables([
        Service,
        Master,
        MasterService,
        Appointment,
        AppointmentService
    ], safe=True)

def populate_initial_data():
    """Заполняет базу начальными данными."""
    if Master.select().count() == 0:
        # Создаем мастеров
        masters_data = [
            {'first_name': 'Иван', 'last_name': 'Иванов', 'phone': '123-456-7890'},
            {'first_name': 'Анна', 'last_name': 'Петрова', 'phone': '987-654-3210'}
        ]
        masters = [Master.create(**data) for data in masters_data]

        # Создаем услуги
        services_data = [
            {'title': 'Стрижка', 'description': 'Классическая стрижка', 'price': 1000.00},
            {'title': 'Бритье', 'description': 'Классическое бритье', 'price': 800.00},
            {'title': 'Укладка', 'description': 'Укладка волос', 'price': 1200.00},
            {'title': 'Окрашивание', 'description': 'Окрашивание волос', 'price': 1500.00},
            {'title': 'Маникюр', 'description': 'Маникюр для мужчин', 'price': 700.00}
        ]
        services = [Service.create(**data) for data in services_data]

        # Связываем мастеров с услугами
        master_services = [
            (masters[0], services[0]), (masters[0], services[1]),
            (masters[1], services[2]), (masters[1], services[3]),
            (masters[0], services[4])
        ]
        for master, service in master_services:
            MasterService.create(master=master, service=service)
