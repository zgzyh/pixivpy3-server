from functools import wraps
from flask import request, jsonify
from app.config import config

def require_auth(f):
    """鉴权装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if token != f"Bearer {config.auth_token}":
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated
