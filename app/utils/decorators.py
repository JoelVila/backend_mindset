from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            identity = get_jwt_identity()
            if identity.get('role') != 'admin':
                return jsonify({"msg": "Acceso denegado: Se requiere rol de Administrador"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper
