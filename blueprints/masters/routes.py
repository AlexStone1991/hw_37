from flask import Blueprint, request, jsonify, Response
from models import Master
from auth import require_api_key, require_admin  # Импортируем оба декоратора
import json
from peewee import IntegrityError

# Создаем блюпринт
masters_bp = Blueprint('masters', __name__, url_prefix='/masters')

@masters_bp.route('/', methods=['GET'])
@require_api_key  # Используем require_api_key вместо require_admin
def get_masters():
    """Получить список всех мастеров"""
    masters = [master_to_dict(master) for master in Master.select()]
    return jsonify({'masters': masters})

@masters_bp.route('/<int:master_id>', methods=['GET'])
@require_api_key
def get_master(master_id):
    """Получить информацию о мастере по ID"""
    try:
        master = Master.get(Master.id == master_id)
        return jsonify(master_to_dict(master))
    except Master.DoesNotExist:
        return Response(
            json.dumps({"error": "Мастер не найден"}, ensure_ascii=False),
            status=404,
            mimetype="application/json; charset=utf-8"
        )

@masters_bp.route('/', methods=['POST'])
@require_admin
def create_master():
    """Создать нового мастера"""
    data = request.get_json()
    if not data or not all(key in data for key in ['first_name', 'last_name', 'phone']):
        return Response(
            json.dumps({"error": "Необходимы first_name, last_name и phone"}, ensure_ascii=False),
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
        return jsonify(master_to_dict(master)), 201
    except IntegrityError:
        return Response(
            json.dumps({"error": "Мастер с таким телефоном уже существует"}, ensure_ascii=False),
            status=400,
            mimetype="application/json; charset=utf-8"
        )

def master_to_dict(master):
    """Преобразует объект Master в словарь"""
    return {
        'id': master.id,
        'first_name': master.first_name,
        'last_name': master.last_name,
        'middle_name': master.middle_name,
        'phone': master.phone
    }
