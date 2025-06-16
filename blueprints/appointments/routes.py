from flask import Blueprint, request, jsonify, Response
from models import Appointment, Master, Service, AppointmentService
from auth import require_api_key, require_admin
import json
from datetime import datetime
from peewee import IntegrityError

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

@appointments_bp.route('/', methods=['GET'])
@require_api_key
def get_appointments():
    """Получить все записи с услугами"""
    sort_by = request.args.get('sort_by', 'date')
    direction = request.args.get('direction', 'asc')

    valid_sort_fields = ['date', 'status', 'client_name']
    if sort_by not in valid_sort_fields:
        sort_by = 'date'

    query = Appointment.select()
    if direction == 'desc':
        query = query.order_by(getattr(Appointment, sort_by).desc())
    else:
        query = query.order_by(getattr(Appointment, sort_by))

    appointments = []
    for appointment in query:
        appointments.append({
            'id': appointment.id,
            'client_name': appointment.client_name,
            'client_phone': appointment.client_phone,
            'date': appointment.date.isoformat(),
            'status': appointment.status,
            'comment': appointment.comment,
            'master': {
                'id': appointment.master.id,
                'first_name': appointment.master.first_name,
                'last_name': appointment.master.last_name
            },
            'services': [aps.service.id for aps in AppointmentService.select().where(AppointmentService.appointment == appointment)]
        })
    return jsonify({'appointments': appointments})

@appointments_bp.route('/<int:appointment_id>', methods=['GET'])
@require_api_key
def get_appointment(appointment_id):
    """Получить запись по ID с услугами"""
    try:
        appointment = Appointment.get(Appointment.id == appointment_id)
        return jsonify({
            'id': appointment.id,
            'client_name': appointment.client_name,
            'client_phone': appointment.client_phone,
            'date': appointment.date.isoformat(),
            'status': appointment.status,
            'comment': appointment.comment,
            'master': {
                'id': appointment.master.id,
                'first_name': appointment.master.first_name,
                'last_name': appointment.master.last_name
            },
            'services': [aps.service.id for aps in AppointmentService.select().where(AppointmentService.appointment == appointment)]
        })
    except Appointment.DoesNotExist:
        return Response(
            json.dumps({"error": "Запись не найдена"}, ensure_ascii=False),
            status=404,
            mimetype="application/json; charset=utf-8"
        )

@appointments_bp.route('/master/<int:master_id>', methods=['GET'])
@require_api_key
def get_appointments_by_master(master_id):
    """Получить записи по мастеру с услугами"""
    try:
        appointments = []
        for appointment in Appointment.select().where(Appointment.master == master_id):
            appointments.append({
                'id': appointment.id,
                'client_name': appointment.client_name,
                'client_phone': appointment.client_phone,
                'date': appointment.date.isoformat(),
                'status': appointment.status,
                'comment': appointment.comment,
                'services': [aps.service.id for aps in AppointmentService.select().where(AppointmentService.appointment == appointment)]
            })
        return jsonify({'appointments': appointments})
    except Master.DoesNotExist:
        return Response(
            json.dumps({"error": "Мастер не найден"}, ensure_ascii=False),
            status=404,
            mimetype="application/json; charset=utf-8"
        )

@appointments_bp.route('/', methods=['POST'])
@require_admin
def create_appointment():
    """Создать новую запись с услугами"""
    data = request.get_json()
    required_fields = ['client_name', 'client_phone', 'master_id', 'date']
    if not data or not all(key in data for key in required_fields):
        return Response(
            json.dumps({"error": f"Необходимы {', '.join(required_fields)}"}, ensure_ascii=False),
            status=400,
            mimetype="application/json; charset=utf-8"
        )

    try:
        appointment = Appointment.create(
            client_name=data['client_name'],
            client_phone=data['client_phone'],
            date=datetime.fromisoformat(data['date']),
            status=data.get('status', 'ожидает'),
            comment=data.get('comment'),
            master=data['master_id']
        )

        # Добавляем услуги к записи, если они указаны
        if 'services' in data:
            for service_id in data['services']:
                AppointmentService.create(
                    appointment=appointment,
                    service=service_id
                )

        return jsonify({
            'id': appointment.id,
            'client_name': appointment.client_name,
            'client_phone': appointment.client_phone,
            'date': appointment.date.isoformat(),
            'status': appointment.status,
            'comment': appointment.comment,
            'master': appointment.master.id,
            'services': data.get('services', [])
        }), 201
    except (Master.DoesNotExist, ValueError) as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            status=400,
            mimetype="application/json; charset=utf-8"
        )

@appointments_bp.route('/<int:appointment_id>', methods=['PUT'])
@require_admin
def update_appointment(appointment_id):
    """Обновить запись и её услуги"""
    data = request.get_json()
    if not data:
        return Response(
            json.dumps({"error": "Нет данных для обновления"}, ensure_ascii=False),
            status=400,
            mimetype="application/json; charset=utf-8"
        )

    try:
        appointment = Appointment.get(Appointment.id == appointment_id)
        if 'client_name' in data:
            appointment.client_name = data['client_name']
        if 'client_phone' in data:
            appointment.client_phone = data['client_phone']
        if 'date' in data:
            appointment.date = datetime.fromisoformat(data['date'])
        if 'status' in data:
            appointment.status = data['status']
        if 'comment' in data:
            appointment.comment = data['comment']
        if 'master_id' in data:
            appointment.master = data['master_id']
        appointment.save()

        # Обновляем услуги записи
        if 'services' in data:
            AppointmentService.delete().where(AppointmentService.appointment == appointment).execute()
            for service_id in data['services']:
                AppointmentService.create(
                    appointment=appointment,
                    service=service_id
                )

        return jsonify({
            'id': appointment.id,
            'client_name': appointment.client_name,
            'client_phone': appointment.client_phone,
            'date': appointment.date.isoformat(),
            'status': appointment.status,
            'comment': appointment.comment,
            'master': appointment.master.id,
            'services': data.get('services', [])
        })
    except Appointment.DoesNotExist:
        return Response(
            json.dumps({"error": "Запись не найдена"}, ensure_ascii=False),
            status=404,
            mimetype="application/json; charset=utf-8"
        )

@appointments_bp.route('/<int:appointment_id>', methods=['DELETE'])
@require_admin
def delete_appointment(appointment_id):
    """Удалить запись"""
    try:
        appointment = Appointment.get(Appointment.id == appointment_id)
        # Удаляем все услуги записи
        AppointmentService.delete().where(AppointmentService.appointment == appointment).execute()
        # Удаляем запись
        appointment.delete_instance()
        return Response(
            json.dumps({"message": "Запись удалена"}, ensure_ascii=False),
            status=200,
            mimetype="application/json; charset=utf-8"
        )
    except Appointment.DoesNotExist:
        return Response(
            json.dumps({"error": "Запись не найдена"}, ensure_ascii=False),
            status=404,
            mimetype="application/json; charset=utf-8"
        )
