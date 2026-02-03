from flask import Blueprint, request, jsonify
from app import db
from app.models import Psicologo, Paciente, Administrador, Especialidad
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login para Psicólogos
    ---
    tags:
      - Auth (Psicólogos)
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login exitoso
        schema:
          type: object
          properties:
            access_token:
              type: string
            role:
              type: string
            user:
              type: object
      401:
        description: Credenciales inválidas
    """
    data = request.get_json()
    response, status_code = AuthService.login(data)
    return jsonify(response), status_code

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registro para nuevos Psicólogos
    ---
    tags:
      - Psicologos
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
            apellido:
              type: string
            email:
              type: string
            password:
              type: string
            numero_colegiado:
              type: string
            especialidades:
              type: array
              items:
                type: integer
    responses:
      201:
        description: Usuario creado exitosamente
      400:
        description: Datos inválidos o usuario ya existe
    """
    data = request.get_json()
    response, status_code = AuthService.register(data)
    return jsonify(response), status_code

@auth_bp.route('/especialidades', methods=['GET'])
def get_especialidades():
    """Get all available specialties"""
    from app.services.general_service import EspecialidadService
    especialidades = EspecialidadService.get_all()
    return jsonify([
        {'id': esp.id_especialidad, 'nombre': esp.nombre}
        for esp in especialidades
    ]), 200
