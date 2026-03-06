from functools import wraps
from flask import request, current_app, jsonify


def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key")
        expected = current_app.config.get("API_KEY")
        if expected and key == expected:
            return func(*args, **kwargs)
        return jsonify({"error": "unauthorized"}), 401

    return wrapper
