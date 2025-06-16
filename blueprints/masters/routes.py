from flask import Blueprint, request, jsonify, Response
from models import Master, Service, MasterService, Appointment
from auth import require_api_key, require_admin
import json
from peewee import IntegrityError

masters_bp = Blueprint('masters', __name__, url_prefix='/masters')

@masters_bp.route('/', methods=['GET'])
@require_api_key
def get_masters():
    """Получить список всех мастеров с их услугами"""
    masters = []
    for master in Master.select():
        masters.append({
            'id': master.id,
            'first_name': master.first_name,
            'last_name': master.last_name,
            'middle_name': master.middle_name,
            'phone': master.phone,
            'services': [ms.service.id for ms in MasterService.select().where(MasterService.master == master)]
        })
    return jsonify({'masters': masters})

@masters_bp.route('/<int:master_id>', methods=['GET'])
@require_api_key
def get_master(master_id):
    """Получить информацию о мастере по ID с его услугами"""
    try:
        master = Master.get(Master.id == master_id)
        return jsonify({
            'id': master.id,
            'first_name': master.first_name,
            'last_name': master.last_name,
            'middle_name': master.middle_name,
            'phone': master.phone,
            'services': [ms.service.id for ms in MasterService.select().where(MasterService.master == master)]
        })
    except Master.DoesNotExist:
        return Response(
            json.dumps({"error": "Мастер не найден"}, ensure_ascii=False),
            status=404,
            mimetype="application/json; charset=utf-8"
        )

@masters_bp.route('/', methods=['POST'])
@require_admin
def create_master():
    """Создать нового мастера с услугами"""
    data = request.get_json()
    required_fields = ['first_name', 'last_name', 'phone']
    if not data or not all(key in data for key in required_fields):
        return Response(
            json.dumps({"error": f"Необходимы {', '.join(required_fields)}"}, ensure_ascii=False),
            status=400,
            mimetype="application/json; charset=utf-8"
        )

    try:
        master = Master.create(
            first_name=data['first_name'],
            last_name=data['last_name'],
            middle_name=data.get('middle_name'),
            phone=data['phone']
        )

        # Добавляем услуги мастера, если они указаны
        if 'services' in data:
            for service_id in data['services']:
                MasterService.create(master=master, service=service_id)

        return jsonify({
            'id': master.id,
            'first_name': master.first_name,
            'last_name': master.last_name,
            'middle_name': master.middle_name,
            'phone': master.phone,
            'services': data.get('services', [])
        }), 201
    except IntegrityError as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            status=400,
            mimetype="application/json; charset=utf-8"
        )

@masters_bp.route('/<int:master_id>', methods=['PUT'])
@require_admin
def update_master(master_id):
    """Обновить информацию о мастере и его услугах"""
    data = request.get_json()
    if not data:
        return Response(
            json.dumps({"error": "Нет данных для обновления"}, ensure_ascii=False),
            status=400,
            mimetype="application/json; charset=utf-8"
        )

    try:
        master = Master.get(Master.id == master_id)
        if 'first_name' in data:
            master.first_name = data['first_name']
        if 'last_name' in data:
            master.last_name = data['last_name']
        if 'middle_name' in data:
            master.middle_name = data['middle_name']
        if 'phone' in data:
            master.phone = data['phone']
        master.save()

        # Обновляем услуги мастера
        if 'services' in data:
            MasterService.delete().where(MasterService.master == master).execute()
            for service_id in data['services']:
                MasterService.create(master=master, service=service_id)

        return jsonify({
            'id': master.id,
            'first_name': master.first_name,
            'last_name': master.last_name,
            'middle_name': master.middle_name,
            'phone': master.phone,
            'services': data.get('services', [])
        })
    except Master.DoesNotExist:
        return Response(
            json.dumps({"error": "Мастер не найден"}, ensure_ascii=False),
            status=404,
            mimetype="application/json; charset=utf-8"
        )

@masters_bp.route('/<int:master_id>', methods=['DELETE'])
@require_admin
def delete_master(master_id):
    """Удалить мастера"""
    try:
        master = Master.get(Master.id == master_id)
        # Удаляем все связанные записи
        Appointment.delete().where(Appointment.master == master).execute()
        # Удаляем все связи с услугами
        MasterService.delete().where(MasterService.master == master).execute()
        # Удаляем мастера
        master.delete_instance()
        return Response(
            json.dumps({"message": "Мастер удален"}, ensure_ascii=False),
            status=200,
            mimetype="application/json; charset=utf-8"
        )
    except Master.DoesNotExist:
        return Response(
            json.dumps({"error": "Мастер не найден"}, ensure_ascii=False),
            status=404,
            mimetype="application/json; charset=utf-8"
        )
