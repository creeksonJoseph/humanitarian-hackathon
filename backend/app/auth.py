import jwt
from functools import wraps
from flask import request, current_app, jsonify
from datetime import datetime, timedelta, timezone

from .errors import ApplicationError
from .models.admin import Admin

def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key")
        expected = current_app.config.get("API_KEY")
        if expected and key == expected:
            return func(*args, **kwargs)
        raise ApplicationError(status_code=401, code="unauthorized", message="Invalid API key")
    return wrapper

def require_jwt(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Allow CORS preflight requests to pass through without a token
        if request.method == "OPTIONS":
            return func(*args, **kwargs)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise ApplicationError(status_code=401, code="unauthorized", message="Missing or invalid Authorization header")
        
        token = auth_header.split(" ")[1]
        secret = current_app.config.get("SECRET_KEY", "default-dev-key")
        
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            request.admin_id = payload.get("sub")
        except jwt.ExpiredSignatureError:
            raise ApplicationError(status_code=401, code="token_expired", message="Token has expired")
        except jwt.InvalidTokenError:
            raise ApplicationError(status_code=401, code="invalid_token", message="Invalid token")
            
        return func(*args, **kwargs)
    return wrapper

def register_auth_routes(bp):
    @bp.route("/login", methods=["POST"])
    def login():
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            raise ApplicationError(status_code=400, code="bad_request", message="Username and password are required")
            
        admin = Admin.query.filter_by(username=username).first()
        if not admin or not admin.check_password(password):
            raise ApplicationError(status_code=401, code="unauthorized", message="Invalid credentials")
            
        secret = current_app.config.get("SECRET_KEY", "default-dev-key")
        exp = datetime.now(timezone.utc) + timedelta(hours=24)
        
        token = jwt.encode(
            {"sub": admin.id, "username": admin.username, "exp": exp},
            secret,
            algorithm="HS256"
        )
        
        return jsonify({"token": token, "username": admin.username})
