from flask import Response, request
from functools import wraps
import json

USERS = [
    {"username": "admin", "api_key": "admin_secret_key_123", "role": "admin"},
    {"username": "user", "api_key": "user_readonly_key_456", "role": "user"}
]

def require_api_key(f):
    """Декоратор для проверки API-ключа"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('api_key')
        if not api_key or not any(user["api_key"] == api_key for user in USERS):
            return Response(
                json.dumps({"error": "Неверный API-ключ"}, ensure_ascii=False),
                status=403,
                mimetype="application/json; charset=utf-8"
            )
        return f(*args, **kwargs)
    return wrapper

def require_admin(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('api_key')
        if not any(user["api_key"] == api_key and user["role"] == "admin" for user in USERS):
            return Response(
                json.dumps({"error": "Требуются права администратора"}, ensure_ascii=False),
                status=403,
                mimetype="application/json; charset=utf-8"
            )
        return f(*args, **kwargs)
    return wrapper


