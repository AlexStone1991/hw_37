from flask import Blueprint, request, jsonify, Response
from models import Appointment, Master
from auth import require_api_key, require_admin
import json
from datetime import datetime
from peewee import IntegrityError

# Создаем блюпринт
appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

@appointments_bp.route('/', methods=['GET'])
@require_api_key
def get_appointments():
    """Получить все записи с опциональной сортировкой"""
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

    appointments = [appointment_to_dict(appointment) for appointment in query]
    return jsonify({'appointments': appointments})

@appointments_bp.route('/<int:appointment_id>', methods=['GET'])
@require_api_key
def get_appointment(appointment_id):
    """Получить запись по ID"""
    try:
        appointment = Appointment.get(Appointment.id == appointment_id)
        return jsonify(appointment_to_dict(appointment))
    except Appointment.DoesNotExist:
        return Response(
            json.dumps({"error": "Запись не найдена"}, ensure_ascii=False),
            status=404,
            mimetype="application/json; charset=utf-8"
        )

def appointment_to_dict(appointment):
    """Преобразует объект Appointment в словарь"""
    return {
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
        }
    }
