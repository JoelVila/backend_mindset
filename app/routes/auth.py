from flask import Blueprint, request, jsonify
from app import db
from app.models import Psicologo, Paciente, Administrador, Especialidad
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    response, status_code = AuthService.login(data)
    return jsonify(response), status_code

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    response, status_code = AuthService.register(data)
    return jsonify(response), status_code

@auth_bp.route('/especialidades', methods=['GET'])
def get_especialidades():
    """Get all available specialties"""
    from app.services.general_service import EspecialidadService
    especialidades = EspecialidadService.get_all()
    return jsonify([
        {'id': esp.id, 'nombre': esp.nombre}
        for esp in especialidades
    ]), 200
