from flask import Blueprint, request, jsonify
from app import db
from app.models import Psicologo, Paciente, Cita, Especialidad, Anamnesis, Informe, Factura, Notificacion
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import json
import re
from app.services.psicologo_service import PsicologoService
from app.services.cita_service import CitaService
from app.services.general_service import InformeService, HistorialService, FacturaService, EspecialidadService
from app.adapters.ocr_adapter import OCRAdapter
from app.adapters.copc_adapter import CopcAdapter

def get_current_user_helper():
    """
    Helper to retrieve and parse JWT identity.
    Handles compatibility between JSON string (legacy/library) and Dict.
    """
    identity = get_jwt_identity()
    if isinstance(identity, str):
        try:
            return json.loads(identity)
        except:
            return identity
    return identity

main_bp = Blueprint('main', __name__)

# --- Especialidades ---
@main_bp.route('/especialidades', methods=['GET'])
def get_especialidades():
    """
    Obtener todas las especialidades
    ---
    tags:
      - General
    responses:
      200:
        description: Lista de especialidades
    """
    especialidades = EspecialidadService.get_all()
    result = []
    for e in especialidades:
        result.append({
            'id': e.id_especialidad,
            'nombre': e.nombre
        })
    return jsonify(result), 200

# --- Psicologos ---
@main_bp.route('/psicologos', methods=['GET'])
@jwt_required()
def get_psicologos():
    """
    Obtener lista básica de psicólogos (Autenticado)
    ---
    tags:
      - Psicologos
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de psicólogos
        schema:
          type: array
          items:
            type: object
            properties:
              id_psicologo:
                type: integer
              nombre:
                type: string
              email:
                type: string
              especialidad:
                type: string
    """
    psicologos = PsicologoService.get_all_basic()
    result = []
    for p in psicologos:
        # Get primary specialty if exists
        esp_nombre = p.especialidades[0].nombre if p.especialidades else None
        
        result.append({
            'id_psicologo': p.id_psicologo,
            'nombre': p.nombre,
            'email': p.correo_electronico,
            'especialidad': esp_nombre
        })
    return jsonify(result), 200

# --- Enhanced Psicologos Search (Public) ---
@main_bp.route('/psicologos/search', methods=['GET'])
def search_psicologos():
    """
    Búsqueda pública de psicólogos
    ---
    tags:
      - Psicologos
    parameters:
      - name: especialidad
        in: query
        type: string
        description: Filtrar por especialidad ID
      - name: nombre
        in: query
        type: string
        description: Filtrar por nombre
    responses:
      200:
        description: Lista detallada de psicólogos
    """
    psicologos = PsicologoService.search_psicologos(request.args)
    
    result = []
    for p in psicologos:
        # Get all specialties
        especialidades_list = [esp.nombre for esp in p.especialidades]
        
        result.append({
            'id_psicologo': p.id_psicologo,
            'nombre': p.nombre,
            'foto_perfil': p.foto_psicologo,
            'especialidades': especialidades_list,
            'email': p.correo_electronico,
            'telefono': p.telefono,
            'numero_colegiado': p.numero_colegiado,
            # Campos recuperados
            'bio': p.bio,
            'anios_experiencia': p.anios_experiencia,
            'precio_presencial': float(p.precio_presencial) if p.precio_presencial else None,
            'precio_online': float(p.precio_online) if p.precio_online else None
        })
    
    return jsonify(result), 200


# --- Get Psychologist Availability by Date (Public) ---
@main_bp.route('/psicologos/<int:id_psicologo>/disponibilidad', methods=['GET'])
def get_disponibilidad_psicologo(id_psicologo):
    """
    Obtener disponibilidad de un psicólogo
    ---
    tags:
      - Psicologos
      - Citas
    parameters:
      - name: id_psicologo
        in: path
        type: integer
        required: true
      - name: fecha
        in: query
        type: string
        description: Fecha en formato YYYY-MM-DD
    responses:
      200:
        description: Horarios disponibles
      404:
        description: Psicólogo no encontrado
    """
    data, error, status = CitaService.get_disponibilidad_psicologo(id_psicologo, request.args.get('fecha'))
    if error:
        return jsonify(error), status
    return jsonify(data), status


# --- Book Appointment (Authenticated) ---
@main_bp.route('/citas/agendar', methods=['POST'])
@jwt_required()
def agendar_cita():
    """
    Agendar una nueva cita (Pacientes)
    ---
    tags:
      - Citas
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            id_psicologo:
              type: integer
            fecha:
              type: string
              format: date
              example: "2024-12-31"
            hora:
              type: string
              format: time
              example: "10:00"
            motivo:
              type: string
    responses:
      201:
        description: Cita creada exitosamente
      403:
        description: Solo pacientes
      400:
        description: Datos inválidos o fecha ocupada
    """
    current_user = get_current_user_helper()

    # Verificar que es un paciente
    if not isinstance(current_user, dict) or current_user.get('role') != 'paciente':
        return jsonify({"msg": "Solo pacientes pueden agendar citas"}), 403
    
    data = request.get_json()
    
    # Call Service
    nueva_cita, error_response, status_code = CitaService.agendar_cita(current_user['id'], data)
    
    if error_response:
        return jsonify(error_response), status_code
    
    psicologo = nueva_cita.psicologo
    
    return jsonify({
        "msg": "Cita agendada exitosamente",
        "cita": {
            "id": nueva_cita.id_cita,
            "fecha": str(nueva_cita.fecha),
            "hora": str(nueva_cita.hora),
            "tipo_cita": nueva_cita.tipo_cita,
            "precio": float(nueva_cita.precio_cita) if nueva_cita.precio_cita else 0,
            "estado": nueva_cita.estado,
            "psicologo": {
                "id": psicologo.id_psicologo,
                "nombre": psicologo.nombre
            },
           "motivo": nueva_cita.motivo,
           "es_primera_vez": nueva_cita.es_primera_vez,
           "id_especialidad": nueva_cita.id_especialidad
        }
    }), 201


# --- Update Psychologist Profile (Authenticated) ---
@main_bp.route('/psicologos/perfil', methods=['PUT'])
@jwt_required()
def update_perfil_psicologo():
    """
    Actualizar perfil (Psicólogos)
    ---
    tags:
      - Psicologos
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nombre:
               type: string
            bio:
               type: string
            precio_presencial:
               type: number
            precio_online:
               type: number
    responses:
      200:
        description: Perfil actualizado
    """
    current_user = get_jwt_identity()
    
    if not isinstance(current_user, dict) or current_user.get('role') != 'psicologo':
        return jsonify({"msg": "Acceso denegado - Solo psicólogos"}), 403
    
    psicologo, error, status = PsicologoService.update_profile(current_user['id'], request.get_json())
    if error:
        return jsonify(error), status
    
    return jsonify({
        "msg": "Perfil actualizado correctamente",
        "psicologo": {
            "id_psicologo": psicologo.id_psicologo,
            "nombre": psicologo.nombre,
            "email": psicologo.correo_electronico,
            "numero_colegiado": psicologo.numero_colegiado,
            "precio_presencial": float(psicologo.precio_presencial) if psicologo.precio_presencial else None,
            "precio_online": float(psicologo.precio_online) if psicologo.precio_online else None,
            "precio_telefono": float(psicologo.precio_telefono) if psicologo.precio_telefono else None,
            "precio_urgencia": float(psicologo.precio_urgencia) if psicologo.precio_urgencia else None,
            "bio": psicologo.bio
        }
    }), 200


# --- Get Psychologist Own Profile (Authenticated) ---
@main_bp.route('/psicologos/perfil', methods=['GET'])
@jwt_required()
def get_perfil_psicologo():
    """
    Obtener mi perfil (Psicólogos)
    ---
    tags:
      - Psicologos
    security:
      - Bearer: []
    responses:
      200:
        description: Datos del perfil del psicólogo autenticado
    """
    current_user = get_jwt_identity()
    
    if not isinstance(current_user, dict) or current_user.get('role') != 'psicologo':
        return jsonify({"msg": "Acceso denegado"}), 403
    
    psicologo = PsicologoService.get_profile(current_user['id'])
    if not psicologo:
        return jsonify({"msg": "Psicólogo no encontrado"}), 404
    
    return jsonify({
        "id_psicologo": psicologo.id_psicologo,
        "nombre": psicologo.nombre,
        "apellido": psicologo.apellido,
        "email": psicologo.correo_electronico,
        "telefono": psicologo.telefono,
        "foto_perfil": psicologo.foto_psicologo,
        "numero_colegiado": psicologo.numero_colegiado,
        "direccion_fiscal": psicologo.direccion_fiscal,
        "dni_nif": psicologo.dni_nif,
        "cuenta_bancaria": psicologo.cuenta_bancaria,
        "especialidades": [{"id": e.id_especialidad, "nombre": e.nombre} for e in psicologo.especialidades],
        # Campos recuperados
        "bio": psicologo.bio,
        "anios_experiencia": psicologo.anios_experiencia,
        "precio_presencial": float(psicologo.precio_presencial) if psicologo.precio_presencial else None,
        "precio_online": float(psicologo.precio_online) if psicologo.precio_online else None,
        "precio_telefono": float(psicologo.precio_telefono) if psicologo.precio_telefono else None,
        "precio_urgencia": float(psicologo.precio_urgencia) if psicologo.precio_urgencia else None,
        "banco": psicologo.banco,
        "titular_cuenta": psicologo.titular_cuenta
    }), 200

# --- Citas ---
@main_bp.route('/citas', methods=['POST'])
@jwt_required()
def create_cita():
    """
    Crear cita (Admin/Interno)
    ---
    tags:
      - Citas
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
    responses:
      201:
        description: Cita creada
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    CitaService.create_simple_cita(data, current_user.get('role'), current_user.get('id'))
    return jsonify({"msg": "Cita created"}), 201

@main_bp.route('/citas', methods=['GET'])
@jwt_required()
def get_citas():
    """
    Obtener todas las citas (Admin)
    ---
    tags:
      - Citas
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de todas las citas
    """
    citas = Cita.query.all()
    result = []
    for c in citas:
        result.append({
            'id': c.id_cita,
            'fecha': str(c.fecha),
            'hora': str(c.hora),
            'psicologo': c.psicologo.nombre,
            'paciente': c.paciente.nombre,
            'estado': c.estado,
            'tipo_cita': c.tipo_cita,
            'precio_cita': float(c.precio_cita) if c.precio_cita else 0
        })
    return jsonify(result), 200

@main_bp.route('/citas/<int:id_cita>', methods=['PUT'])
@jwt_required()
def update_cita(id_cita):
    """
    Actualizar Cita (Cancelar/Reprogramar)
    ---
    tags:
      - Citas
    security:
      - Bearer: []
    parameters:
      - name: id_cita
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            fecha:
              type: string
            hora:
              type: string
            estado:
              type: string
              enum: ['cancelada', 'confirmada']
            motivo:
              type: string
    responses:
      200:
        description: Cita actualizada
      403:
        description: No autorizado
    """
    current_user = get_jwt_identity()
    result, msg, code = CitaService.update_cita(id_cita, request.get_json(), current_user['id'], current_user['role'])
    if result:
         return jsonify(msg), code
    return jsonify(msg), code

# --- Get Psychologist's Appointments (Authenticated) ---
@main_bp.route('/psicologos/citas', methods=['GET'])
@jwt_required()
def get_citas_psicologo():
    """
    Obtener citas del psicólogo
    ---
    tags:
      - Citas
      - Psicologos
    security:
      - Bearer: []
    parameters:
      - name: estado
        in: query
        type: string
        description: Filtrar por estado (proximas, pasadas...)
    responses:
      200:
        description: Lista de citas
    """
    current_user = get_jwt_identity()
    
    if not isinstance(current_user, dict) or current_user.get('role') != 'psicologo':
        return jsonify({"msg": "Acceso denegado - Solo psicólogos"}), 403
    
    citas = CitaService.get_citas_psicologo(current_user['id'], request.args.get('estado', 'proximas'))
    
    result = []
    for cita in citas:
        paciente = cita.paciente
        result.append({
            'id_cita': cita.id_cita,
            'fecha': str(cita.fecha),
            'hora': str(cita.hora),
            'estado': cita.estado,
            'tipo_cita': cita.tipo_cita,
            'precio': float(cita.precio_cita) if cita.precio_cita else 0,
            'paciente': {
                'id': paciente.id_paciente,
                'nombre': paciente.nombre,
                'apellido': paciente.apellido,
                'email': paciente.correo_electronico,
                'telefono': paciente.telefono
            }
        })
    
    return jsonify(result), 200

# --- Get Patient's Appointments (Authenticated) ---
@main_bp.route('/pacientes/citas', methods=['GET'])
@jwt_required()
def get_citas_paciente():
    """
    Obtener citas del paciente
    ---
    tags:
      - Citas
      - Pacientes
    security:
      - Bearer: []
    parameters:
      - name: estado
        in: query
        type: string
        description: Filtrar por estado (proximas, pasadas...)
    responses:
      200:
        description: Lista de citas
    """
    current_user = get_jwt_identity()
    
    if not isinstance(current_user, dict) or current_user.get('role') != 'paciente':
        return jsonify({"msg": "Acceso denegado - Solo pacientes"}), 403
    
    citas = CitaService.get_citas_paciente(current_user['id'], request.args.get('estado', 'proximas'))
    
    result = []
    for cita in citas:
        psicologo = cita.psicologo
        result.append({
            'id_cita': cita.id_cita,
            'fecha': str(cita.fecha),
            'hora': str(cita.hora),
            'estado': cita.estado,
            'tipo_cita': cita.tipo_cita,
            'precio': float(cita.precio_cita) if cita.precio_cita else 0,
            'psicologo': {
                'id': psicologo.id_psicologo,
                'nombre': psicologo.nombre,
                'foto_perfil': psicologo.foto_psicologo,
                'email': psicologo.correo_electronico,
                'telefono': psicologo.telefono,
                'especialidades': [esp.nombre for esp in psicologo.especialidades]
            }
        })
    return jsonify(result), 200

# --- Historial Clinico (NOW ANAMNESIS) ---
@main_bp.route('/historial/<int:paciente_id>', methods=['GET'])
@jwt_required()
def get_historial(paciente_id):
    """
    Obtener historial clínico
    ---
    tags:
      - Historial
    security:
      - Bearer: []
    parameters:
      - name: paciente_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Historial del paciente
      404:
        description: No encontrado
    """
    # This might need adapting to Anamnesis model or using the old service updated
    historial = HistorialService.get_historial(paciente_id)
    if not historial:
        return jsonify({"msg": "No history found"}), 404
    return jsonify({
        'contenido': getattr(historial, 'contenido', ''),# Helper might map to anamnesis fields
        'fecha_creacion': getattr(historial, 'fecha_creacion', None)
    }), 200

@main_bp.route('/historial', methods=['POST'])
@jwt_required()
def update_historial():
    """
    Actualizar historial clínico
    ---
    tags:
      - Historial
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
    responses:
      200:
        description: Historial actualizado
    """
    HistorialService.update_historial(request.get_json())
    return jsonify({"msg": "Historial updated"}), 200

# --- Informes ---

# Get Patient's Reports (Authenticated - Patients only)
@main_bp.route('/pacientes/informes', methods=['GET'])
@jwt_required()
def get_informes_paciente():
    """
    Ver mis informes (Pacientes)
    ---
    tags:
      - Informes
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de informes del paciente
    """
    current_user = get_jwt_identity()
        
    if not isinstance(current_user, dict) or current_user.get('role') != 'paciente':
        return jsonify({"msg": "Acceso denegado - Solo pacientes"}), 403
    
    informes = InformeService.get_informes_paciente(current_user['id'])
    
    result = []
    for informe in informes:
        psicologo = informe.psicologo
        result.append({
            'id_informe': informe.id_informe,
            'psicologo': {
                'id': psicologo.id_psicologo,
                'nombre': psicologo.nombre,
                'foto_perfil': psicologo.foto_psicologo,
                'especialidades': [esp.nombre for esp in psicologo.especialidades]
            },
            'contenido': informe.texto_informe, # Changed from contenido to texto_informe possibly? Check model. Model has texto_informe
            'titulo': informe.titulo_informe,
            'fecha_creacion': informe.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_modificacion': informe.fecha_modificacion.strftime('%Y-%m-%d %H:%M:%S') if informe.fecha_modificacion else None
        })
    return jsonify(result), 200


# Get Psychologist's Reports (Authenticated - Psychologists only)
@main_bp.route('/psicologos/informes', methods=['GET'])
@jwt_required()
def get_informes_psicologo():
    """
    Ver informes creados (Psicólogos)
    ---
    tags:
      - Informes
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de informes creados por el psicólogo
    """
    current_user = get_jwt_identity()
    
    if not isinstance(current_user, dict) or current_user.get('role') != 'psicologo':
        return jsonify({"msg": "Acceso denegado - Solo psicólogos"}), 403
    
    informes = InformeService.get_informes_psicologo(current_user['id'])
    
    result = []
    for informe in informes:
        paciente = informe.paciente
        result.append({
            'id_informe': informe.id_informe,
            'paciente': {
                'id': paciente.id_paciente,
                'nombre': paciente.nombre,
                'apellido': paciente.apellido,
                'email': paciente.correo_electronico
            },
            'contenido': informe.texto_informe,
            'titulo': informe.titulo_informe,
            'fecha_creacion': informe.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_modificacion': informe.fecha_modificacion.strftime('%Y-%m-%d %H:%M:%S') if informe.fecha_modificacion else None
        })
    return jsonify(result), 200


# Get Specific Report Details
@main_bp.route('/informes/<int:id_informe>', methods=['GET'])
@jwt_required()
def get_informe_detalle(id_informe):
    """
    Ver detalle de informe
    ---
    tags:
      - Informes
    security:
      - Bearer: []
    parameters:
      - name: id_informe
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Detalle del informe
    """
    current_user = get_jwt_identity()

    informe, error, status = InformeService.get_informe_detalle(id_informe, current_user.get('id'), current_user.get('role'))
    if error:
        return jsonify(error), status
    
    psicologo = informe.psicologo
    paciente = informe.paciente
    
    return jsonify({
        'id_informe': informe.id_informe,
        'psicologo': {
            'id': psicologo.id_psicologo,
            'nombre': psicologo.nombre,
            'foto_perfil': psicologo.foto_psicologo,
            'especialidades': [esp.nombre for esp in psicologo.especialidades]
        },
        'paciente': {
            'id': paciente.id_paciente,
            'nombre': paciente.nombre,
            'apellido': paciente.apellido
        },
        'contenido': informe.texto_informe,
        'diagnostico': informe.diagnostico,
        'tratamiento': informe.tratamiento,
        'fecha_creacion': informe.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
        'fecha_modificacion': informe.fecha_modificacion.strftime('%Y-%m-%d %H:%M:%S') if informe.fecha_modificacion else None
    }), 200


# Create Report (Psychologists only)
@main_bp.route('/psicologos/informes', methods=['POST'])
@jwt_required()
def create_informe():
    """
    Crear informe (Psicólogos)
    ---
    tags:
      - Informes
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
    responses:
      201:
        description: Informe creado
    """
    current_user = get_jwt_identity()
    
    if not isinstance(current_user, dict) or current_user.get('role') != 'psicologo':
        return jsonify({"msg": "Solo psicólogos pueden crear informes"}), 403
    
    new_informe, error, status = InformeService.create_informe(current_user['id'], request.get_json())
    if error:
        return jsonify(error), status
        
    return jsonify({
        "msg": "Informe creado exitosamente",
        "informe": {
            "id_informe": new_informe.id_informe,
            "id_paciente": new_informe.id_paciente,
            "id_psicologo": new_informe.id_psicologo,
            "fecha_creacion": new_informe.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 201

# --- Facturas ---
@main_bp.route('/facturas', methods=['POST'])
@jwt_required()
def create_factura():
    """
    Generar factura
    ---
    tags:
      - Facturacion
    security:
      - Bearer: []
    parameters:
       - in: body
         name: body
         required: true
         schema:
           type: object
    responses:
      201:
        description: Factura creada
    """
    data = request.get_json()
    current_user = get_jwt_identity()

    if not isinstance(current_user, dict) or current_user.get('role') != 'psicologo':
        return jsonify({"msg": "Solo psicólogos pueden crear facturas"}), 403

    # Inject psychologist ID from token
    data['id_psicologo'] = current_user['id']
    
    new_factura = FacturaService.create_factura(data)
    return jsonify({"msg": "Factura created", "id": new_factura.id_factura}), 201

# --- Notificaciones ---
@main_bp.route('/notificaciones', methods=['GET'])
@jwt_required()
def get_notificaciones():
    """
    Obtener notificaciones
    ---
    tags:
      - Notificaciones
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de notificaciones no leídas
    """
    current_user = get_jwt_identity()
    
    if current_user.get('role') == 'paciente':
        notificaciones = Notificacion.query.filter_by(id_paciente=current_user['id']).all()
    elif current_user.get('role') == 'psicologo':
        notificaciones = Notificacion.query.filter_by(id_psicologo=current_user['id']).all()
    else:
        return jsonify([]), 200

    result = [{'mensaje': n.mensaje, 'leida': n.leido} for n in notificaciones]
    return jsonify(result), 200

# --- Auth (Paciente) ---
@main_bp.route('/register_paciente', methods=['POST'])
def register_paciente():
    """
    Registro de Paciente
    ---
    tags:
      - Pacientes
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
             fecha_nacimiento:
               type: string
             dni_nif:
               type: string
    responses:
      201:
        description: Paciente registrado
    """
    data = request.get_json()
    
    if Paciente.query.filter_by(correo_electronico=data.get('email')).first():
            return jsonify({"msg": "Email already exists"}), 400
            
    if 'fecha_nacimiento' not in data:
        return jsonify({"msg": "Falta fecha_nacimiento"}), 400

    fecha_nacim_str = data.get('fecha_nacimiento')
    fecha_nacim = None
    edad = None
    
    try:
        fecha_nacim = datetime.strptime(fecha_nacim_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        edad = today.year - fecha_nacim.year - ((today.month, today.day) < (fecha_nacim.month, fecha_nacim.day))
    except ValueError:
        return jsonify({"msg": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400

    new_user = Paciente(
        nombre=data.get('nombre'),
        correo_electronico=data.get('email'),
        contrasena_hash=generate_password_hash(data.get('password')),
        apellido=data.get('apellido'),
        telefono=data.get('telefono'),
        dni_nif=data.get('dni_nif'),
        foto_paciente=data.get('foto_perfil'),
        fecha_nacimiento=fecha_nacim,
        edad=edad
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "Paciente created successfully"}), 201

@main_bp.route('/login_paciente', methods=['POST'])
def login_paciente():
    """
    Login de Paciente
    ---
    tags:
      - Auth
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
        description: Login exitoso, retorna Token JWT
        schema:
          type: object
          properties:
            access_token:
              type: string
            role:
              type: string
      401:
        description: Credenciales inválidas
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = Paciente.query.filter_by(correo_electronico=email).first()
    if user and check_password_hash(user.contrasena_hash, password):
        # Already cleaned up AuthService, but this is redundant manual method.
        # Ideally should use AuthService here too, but for consistency fixing return here
        identity_dict = {'id': user.id_paciente, 'role': 'paciente'}
        # Pass dict directly
        access_token = create_access_token(identity=identity_dict)
        return jsonify(access_token=access_token, role='paciente'), 200
    
    return jsonify({"msg": "Bad username or password"}), 401

@main_bp.route('/perfil_paciente', methods=['GET'])
@jwt_required()
def perfil_paciente():
    """
    Obtener mi perfil (Paciente)
    ---
    tags:
      - Pacientes
    security:
      - Bearer: []
    responses:
      200:
        description: Perfil del paciente
    """
    current_user = get_jwt_identity()
        
    if not isinstance(current_user, dict) or current_user.get('role') != 'paciente':
        return jsonify({"msg": "Access denied"}), 403
        
    user = Paciente.query.get(current_user['id'])
    if not user:
        return jsonify({"msg": "User not found"}), 404
        
    return jsonify({
        'id_paciente': user.id_paciente,
        'nombre': user.nombre,
        'apellido': user.apellido,
        'email': user.correo_electronico,
        'telefono': user.telefono,
        'dni_nif': user.dni_nif,
        'foto_perfil': user.foto_paciente,
        # Campos recuperados
        'edad': user.edad,
        'fecha_nacimiento': str(user.fecha_nacimiento) if user.fecha_nacimiento else None
    }), 200


# Update Patient Profile
@main_bp.route('/pacientes/perfil', methods=['PUT'])
@jwt_required()
def update_perfil_paciente():
    """
    Actualizar perfil (Paciente)
    ---
    tags:
      - Pacientes
    security:
      - Bearer: []
    parameters:
       - in: body
         name: body
         required: true
         schema:
           type: object
    responses:
      200:
         description: Perfil actualizado
    """
    current_user = get_current_user_helper()
    
    if not isinstance(current_user, dict) or current_user.get('role') != 'paciente':
        return jsonify({"msg": "Acceso denegado - Solo pacientes"}), 403
    
    user = Paciente.query.get(current_user['id'])
    if not user:
        return jsonify({"msg": "Usuario no encontrado"}), 404
    
    data = request.get_json()
    
    # Actualizar campos permitidos
    if 'nombre' in data:
        user.nombre = data['nombre']
    if 'apellido' in data:
        user.apellido = data['apellido']
    if 'telefono' in data:
        user.telefono = data['telefono']
    if 'dni_nif' in data:
        user.dni_nif = data['dni_nif']
    if 'foto_perfil' in data:
        user.foto_paciente = data['foto_perfil']
    
    # Campo recuperado
    if 'fecha_nacimiento' in data and data['fecha_nacimiento']:
        try:
            user.fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
            # Calcular edad automáticamente
            today = datetime.now().date()
            age = today.year - user.fecha_nacimiento.year - (
                (today.month, today.day) < (user.fecha_nacimiento.month, user.fecha_nacimiento.day)
            )
            user.edad = age
        except ValueError:
            return jsonify({"msg": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
    
    db.session.commit()
    
    return jsonify({
        "msg": "Perfil actualizado correctamente",
        "paciente": {
            "id": user.id_paciente,
            "nombre": user.nombre,
            "apellido": user.apellido,
            "email": user.correo_electronico,
            "telefono": user.telefono,
            "edad": user.edad,
            "fecha_nacimiento": str(user.fecha_nacimiento) if user.fecha_nacimiento else None
        }
    }), 200

# --- OCR Verification ---
@main_bp.route('/analyze-document', methods=['POST'])
def analyze_document():
    try:
        # Inicializar Adapter
        ocr_adapter = OCRAdapter()
        
        # Extraer texto
        result_text_list = ocr_adapter.extract_text(file_content)
        full_text = " ".join(result_text_list)
        
        print(f"Texto extraído: {full_text}")
        
        # Buscar candidatos a Número de Colegiado (1 a 9 dígitos)
        # Ajustamos regex para capturar grupos de digitos
        candidates = re.findall(r'\b\d{1,9}\b', full_text)
        
        adapter = CopcAdapter()
        verified_data = None
        
        # Probar cada candidato contra el COPC
        for num in candidates:
            # Filtro básico: los números muy cortos (1-2 dígitos) suelen ser falsos positivos (fechas, paginas)
            if len(num) < 3: 
                continue
                
            res = adapter.verify(num)
            if res.get("verified"):
                verified_data = res
                break
        
        # Si no se verifica ninguno, devolvemos error con info
        if not verified_data:
            return jsonify({
                 "verified": False,
                 "msg": f"No se pudo verificar ningún número colegiado válido. Texto leído: {full_text[:50]}...",
                 "raw_text": full_text
            }), 400

        result = {
            "numero_licencia": verified_data.get("numero_colegiado"),
            "nombre": verified_data.get("nombre"),
            "verified": True,
            "institucion": verified_data.get("institucion", "COPC"),
            "msg": verified_data.get("msg")
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error OCR: {e}")
        return jsonify({"msg": f"Error procesando el documento: {str(e)}"}), 500


# --- Biometric Verification ---
@main_bp.route('/biometric/verify-identity', methods=['POST'])
def verify_identity():
    """
    Endpoint para verificar identidad mediante comparación facial (DNI vs Selfie).
    Espera 'dni_image' y 'selfie_image' como archivos form-data.
    """
    from app.services.biometric_service import BiometricService

    if 'dni_image' not in request.files or 'selfie_image' not in request.files:
        return jsonify({"msg": "Faltan imágenes (dni_image, selfie_image)"}), 400
    
    dni_file = request.files['dni_image']
    selfie_file = request.files['selfie_image']
    
    if dni_file.filename == '' or selfie_file.filename == '':
        return jsonify({"msg": "Archivos no seleccionados"}), 400

    try:
        service = BiometricService()
        # Leemos los bytes de los archivos
        dni_bytes = dni_file.read()
        selfie_bytes = selfie_file.read()
        
        result = service.verify_identity(dni_bytes, selfie_bytes)
        
        # Si la verificación es exitosa y se proporciona un ID de psicólogo, actualizamos la BD
        if result.get("verified") and 'id_psicologo' in request.form:
            try:
                id_psi = request.form['id_psicologo']
                psicologo = Psicologo.query.get(id_psi)
                if psicologo:
                    psicologo.verificado = True
                    msg_extras = []
                    msg_extras.append("Status verificado actualizado.")

                    # --- Automatic DNI Extraction ---
                    try:
                        ocr_adapter = OCRAdapter()
                        ocr_result = ocr_adapter.extract_text(dni_bytes)
                        full_ocr_text = " ".join(ocr_result)
                        
                        # Regex for DNI (8 digits + letter) or NIE (X/Y/Z + 7 digits + letter)
                        # Simple regex to catch standard formats
                        dni_candidates = re.findall(r'\b(?:[XYZ]\d{7}|[0-9]{8})[- ]?[A-Z]\b', full_ocr_text)
                        
                        if dni_candidates:
                            # Take the first candidate, clean it up
                            extracted_dni = dni_candidates[0].replace(" ", "").replace("-", "")
                            psicologo.dni_nif = extracted_dni
                            msg_extras.append(f"DNI/NIF extraído y actualizado: {extracted_dni}")
                        else:
                            msg_extras.append("No se pudo extraer DNI/NIF legible del documento.")

                    except Exception as ocr_e:
                        print(f"Error OCR en verify_identity: {ocr_e}")
                        msg_extras.append(f"Error extrayendo DNI: {str(ocr_e)}")
                    
                    db.session.commit()
                    result['db_update'] = " | ".join(msg_extras)
            except Exception as e:
                print(f"Error actualizando DB: {e}")
                result['db_error'] = str(e)
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error en biometría: {e}")
        return jsonify({"msg": f"Error procesando verificación biométrica: {str(e)}"}), 500
