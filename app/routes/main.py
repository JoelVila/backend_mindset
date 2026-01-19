from flask import Blueprint, request, jsonify
from app import db
from app.models import Psicologo, Paciente, Cita, Especialidad, HistorialClinico, Informe, Factura, Notificacion, Resena
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import json
from app.services.psicologo_service import PsicologoService
from app.services.cita_service import CitaService
from app.services.general_service import InformeService, HistorialService, FacturaService, EspecialidadService

main_bp = Blueprint('main', __name__)

# --- Especialidades ---
@main_bp.route('/especialidades', methods=['GET'])
def get_especialidades():
    especialidades = EspecialidadService.get_all()
    result = []
    for e in especialidades:
        result.append({
            'id': e.id,
            'nombre': e.nombre
        })
    return jsonify(result), 200

# --- Psicologos ---
@main_bp.route('/psicologos', methods=['GET'])
@jwt_required()
def get_psicologos():
    psicologos = PsicologoService.get_all_basic()
    result = []
    for p in psicologos:
        result.append({
            'id_psicologo': p.id_psicologo,
            'nombre': p.nombre,
            'email': p.email,
            'especialidad': p.especialidad_id
        })
    return jsonify(result), 200

# --- Enhanced Psicologos Search (Public) ---
@main_bp.route('/psicologos/search', methods=['GET'])
def search_psicologos():
    """
    Public endpoint to search psychologists with enhanced data
    """
    psicologos = PsicologoService.search_psicologos(request.args)
    
    result = []
    for p in psicologos:
        # Get rating and review count
        rating_promedio = p.get_rating_promedio()
        num_resenas = p.get_num_resenas()
        
        # Get all specialties
        especialidades_list = [esp.nombre for esp in p.especialidades]
        
        result.append({
            'id_psicologo': p.id_psicologo,
            'nombre': p.nombre,
            'foto_perfil': p.foto_perfil,
            'verificado': p.verificado,
            'rating_promedio': round(rating_promedio, 1) if rating_promedio else None,
            'num_resenas': num_resenas,
            'bio': p.bio,
            'especialidades': especialidades_list,
            'precio_presencial': p.precio_presencial,
            'precio_online': p.precio_online,
            'anios_experiencia': p.anios_experiencia,
            'email': p.email,
            'telefono': p.telefono
        })
    
    return jsonify(result), 200


# --- Get Psychologist Availability by Date (Public) ---
@main_bp.route('/psicologos/<int:id_psicologo>/disponibilidad', methods=['GET'])
def get_disponibilidad_psicologo(id_psicologo):
    data, error, status = CitaService.get_disponibilidad_psicologo(id_psicologo, request.args.get('fecha'))
    if error:
        return jsonify(error), status
    return jsonify(data), status


# --- Book Appointment (Authenticated) ---
@main_bp.route('/citas/agendar', methods=['POST'])
@jwt_required()
def agendar_cita():
    current_user = get_jwt_identity()
    
    # Parse JSON if needed
    if isinstance(current_user, str):
        try:
            current_user = json.loads(current_user)
        except:
            pass
    
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
            "id": nueva_cita.id,
            "fecha": str(nueva_cita.fecha),
            "hora": str(nueva_cita.hora),
            "tipo_cita": nueva_cita.tipo_cita,
            "precio": nueva_cita.precio_cita,
            "estado": nueva_cita.estado,
            "psicologo": {
                "id": psicologo.id_psicologo,
                "nombre": psicologo.nombre
            }
        }
    }), 201


# --- Update Psychologist Profile (Authenticated) ---
@main_bp.route('/psicologos/perfil', methods=['PUT'])
@jwt_required()
def update_perfil_psicologo():
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
            "email": psicologo.email,
            "precio_presencial": psicologo.precio_presencial,
            "precio_online": psicologo.precio_online,
            "precio_chat": psicologo.precio_chat
        }
    }), 200


# --- Get Psychologist Own Profile (Authenticated) ---
@main_bp.route('/psicologos/perfil', methods=['GET'])
@jwt_required()
def get_perfil_psicologo():
    current_user = get_jwt_identity()
    
    if not isinstance(current_user, dict) or current_user.get('role') != 'psicologo':
        return jsonify({"msg": "Acceso denegado"}), 403
    
    psicologo = PsicologoService.get_profile(current_user['id'])
    if not psicologo:
        return jsonify({"msg": "Psicólogo no encontrado"}), 404
    
    return jsonify({
        "id_psicologo": psicologo.id_psicologo,
        "nombre": psicologo.nombre,
        "email": psicologo.email,
        "telefono": psicologo.telefono,
        "bio": psicologo.bio,
        "foto_perfil": psicologo.foto_perfil,
        "verificado": psicologo.verificado,
        "anios_experiencia": psicologo.anios_experiencia,
        "precio_presencial": psicologo.precio_presencial,
        "precio_online": psicologo.precio_online,
        "precio_chat": psicologo.precio_chat,
        "numero_cuenta": psicologo.numero_cuenta,
        "banco": psicologo.banco,
        "titular_cuenta": psicologo.titular_cuenta,
        "especialidades": [{"id": e.id, "nombre": e.nombre} for e in psicologo.especialidades]
    }), 200

# --- Citas ---
@main_bp.route('/citas', methods=['POST'])
@jwt_required()
def create_cita():
    current_user = get_jwt_identity()
    data = request.get_json()
    CitaService.create_simple_cita(data, current_user.get('role'), current_user.get('id'))
    return jsonify({"msg": "Cita created"}), 201

@main_bp.route('/citas', methods=['GET'])
@jwt_required()
def get_citas():
    citas = Cita.query.all()
    result = []
    for c in citas:
        result.append({
            'id': c.id,
            'fecha': str(c.fecha),
            'hora': str(c.hora),
            'psicologo': c.psicologo.nombre,
            'paciente': c.paciente.nombre,
            'estado': c.estado,
            'tipo_cita': c.tipo_cita,
            'precio_cita': c.precio_cita
        })
    return jsonify(result), 200

# --- Get Psychologist's Appointments (Authenticated) ---
@main_bp.route('/psicologos/citas', methods=['GET'])
@jwt_required()
def get_citas_psicologo():
    current_user = get_jwt_identity()
    
    if not isinstance(current_user, dict) or current_user.get('role') != 'psicologo':
        return jsonify({"msg": "Acceso denegado - Solo psicólogos"}), 403
    
    citas = CitaService.get_citas_psicologo(current_user['id'], request.args.get('estado', 'proximas'))
    
    result = []
    for cita in citas:
        paciente = cita.paciente
        result.append({
            'id_cita': cita.id,
            'fecha': str(cita.fecha),
            'hora': str(cita.hora),
            'estado': cita.estado,
            'tipo_cita': cita.tipo_cita,
            'precio': cita.precio_cita,
            'paciente': {
                'id': paciente.id_paciente,
                'nombre': paciente.nombre,
                'apellido': paciente.apellido,
                'email': paciente.email,
                'telefono': paciente.telefono
            }
        })
    
    return jsonify(result), 200

# --- Get Patient's Appointments (Authenticated) ---
@main_bp.route('/pacientes/citas', methods=['GET'])
@jwt_required()
def get_citas_paciente():
    current_user = get_jwt_identity()
    
    if isinstance(current_user, str):
        try: current_user = json.loads(current_user)
        except: pass
    
    if not isinstance(current_user, dict) or current_user.get('role') != 'paciente':
        return jsonify({"msg": "Acceso denegado - Solo pacientes"}), 403
    
    citas = CitaService.get_citas_paciente(current_user['id'], request.args.get('estado', 'proximas'))
    
    result = []
    for cita in citas:
        psicologo = cita.psicologo
        result.append({
            'id_cita': cita.id,
            'fecha': str(cita.fecha),
            'hora': str(cita.hora),
            'estado': cita.estado,
            'tipo_cita': cita.tipo_cita,
            'precio': cita.precio_cita,
            'psicologo': {
                'id': psicologo.id_psicologo,
                'nombre': psicologo.nombre,
                'foto_perfil': psicologo.foto_perfil,
                'email': psicologo.email,
                'telefono': psicologo.telefono,
                'especialidades': [esp.nombre for esp in psicologo.especialidades]
            }
        })
    return jsonify(result), 200

# --- Historial Clinico ---
@main_bp.route('/historial/<int:paciente_id>', methods=['GET'])
@jwt_required()
def get_historial(paciente_id):
    historial = HistorialService.get_historial(paciente_id)
    if not historial:
        return jsonify({"msg": "No history found"}), 404
    return jsonify({
        'contenido': historial.contenido,
        'fecha_creacion': historial.fecha_creacion
    }), 200

@main_bp.route('/historial', methods=['POST'])
@jwt_required()
def update_historial():
    HistorialService.update_historial(request.get_json())
    return jsonify({"msg": "Historial updated"}), 200

# --- Informes ---

# Get Patient's Reports (Authenticated - Patients only)
@main_bp.route('/pacientes/informes', methods=['GET'])
@jwt_required()
def get_informes_paciente():
    current_user = get_jwt_identity()
    if isinstance(current_user, str):
        try: current_user = json.loads(current_user)
        except: pass
        
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
                'foto_perfil': psicologo.foto_perfil,
                'especialidades': [esp.nombre for esp in psicologo.especialidades]
            },
            'contenido': informe.contenido,
            'fecha_creacion': informe.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_modificacion': informe.fecha_modificacion.strftime('%Y-%m-%d %H:%M:%S') if informe.fecha_modificacion else None
        })
    return jsonify(result), 200


# Get Psychologist's Reports (Authenticated - Psychologists only)
@main_bp.route('/psicologos/informes', methods=['GET'])
@jwt_required()
def get_informes_psicologo():
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
                'email': paciente.email
            },
            'contenido': informe.contenido,
            'fecha_creacion': informe.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_modificacion': informe.fecha_modificacion.strftime('%Y-%m-%d %H:%M:%S') if informe.fecha_modificacion else None
        })
    return jsonify(result), 200


# Get Specific Report Details
@main_bp.route('/informes/<int:id_informe>', methods=['GET'])
@jwt_required()
def get_informe_detalle(id_informe):
    current_user = get_jwt_identity()
    if isinstance(current_user, str):
        try: current_user = json.loads(current_user)
        except: pass

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
            'foto_perfil': psicologo.foto_perfil,
            'especialidades': [esp.nombre for esp in psicologo.especialidades]
        },
        'paciente': {
            'id': paciente.id_paciente,
            'nombre': paciente.nombre,
            'apellido': paciente.apellido
        },
        'contenido': informe.contenido,
        'fecha_creacion': informe.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
        'fecha_modificacion': informe.fecha_modificacion.strftime('%Y-%m-%d %H:%M:%S') if informe.fecha_modificacion else None
    }), 200


# Create Report (Psychologists only)
@main_bp.route('/psicologos/informes', methods=['POST'])
@jwt_required()
def create_informe():
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
    data = request.get_json()
    new_factura = FacturaService.create_factura(data)
    return jsonify({"msg": "Factura created", "id": new_factura.id_factura}), 201

# --- Notificaciones ---
@main_bp.route('/notificaciones', methods=['GET'])
@jwt_required()
def get_notificaciones():
    current_user = get_jwt_identity()
    # Assuming we want notifs for the logged in user.
    # We need to check role to know which field to query
    
    if current_user['role'] == 'paciente':
        notificaciones = Notificacion.query.filter_by(id_paciente=current_user['id']).all()
    elif current_user['role'] == 'psicologo':
        notificaciones = Notificacion.query.filter_by(id_psicologo=current_user['id']).all()
    else:
        return jsonify([]), 200

    result = [{'mensaje': n.mensaje, 'leida': n.leida} for n in notificaciones]
    return jsonify(result), 200

# --- Auth (Paciente) ---
@main_bp.route('/register_paciente', methods=['POST'])
def register_paciente():
    data = request.get_json()
    
    if Paciente.query.filter_by(email=data.get('email')).first():
            return jsonify({"msg": "Email already exists"}), 400
            
    new_user = Paciente(
        nombre=data.get('nombre'),
        email=data.get('email'),
        password_hash=generate_password_hash(data.get('password')),
        apellido=data.get('apellido'),
        edad=data.get('edad'),
        telefono=data.get('telefono'),
        tipo_paciente=data.get('tipo_paciente'),
        tipo_tarjeta=data.get('tipo_tarjeta')
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "Paciente created successfully"}), 201

@main_bp.route('/login_paciente', methods=['POST'])
def login_paciente():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = Paciente.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        identity_dict = {'id': user.id_paciente, 'role': 'paciente'}
        access_token = create_access_token(identity=json.dumps(identity_dict))
        return jsonify(access_token=access_token, role='paciente'), 200
    
    return jsonify({"msg": "Bad username or password"}), 401

@main_bp.route('/perfil_paciente', methods=['GET'])
@jwt_required()
def perfil_paciente():
    current_user_json = get_jwt_identity()
    try:
        current_user = json.loads(current_user_json)
    except:
        current_user = current_user_json # Fallback if it's already a dict or simple string
        
    if not isinstance(current_user, dict) or current_user.get('role') != 'paciente':
        return jsonify({"msg": "Access denied"}), 403
        
    user = Paciente.query.get(current_user['id'])
    if not user:
        return jsonify({"msg": "User not found"}), 404
        
    return jsonify({
        'id': user.id_paciente,
        'nombre': user.nombre,
        'apellido': user.apellido,
        'email': user.email,
        'telefono': user.telefono,
        'edad': user.edad,
        'fecha_nacimiento': str(user.fecha_nacimiento) if user.fecha_nacimiento else None,
        'tipo_paciente': user.tipo_paciente
    }), 200


# Update Patient Profile
@main_bp.route('/pacientes/perfil', methods=['PUT'])
@jwt_required()
def update_perfil_paciente():
    """
    Update patient profile information
    Body: {
        "nombre": "Juan",
        "apellido": "Pérez",
        "telefono": "+56912345678",
        "fecha_nacimiento": "1995-05-15"  // Optional, format: YYYY-MM-DD
    }
    """
    current_user_json = get_jwt_identity()
    try:
        current_user = json.loads(current_user_json)
    except:
        current_user = current_user_json
    
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
    if 'fecha_nacimiento' in data and data['fecha_nacimiento']:
        try:
            user.fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
            # Calcular edad automáticamente si se proporciona fecha de nacimiento
            from datetime import date
            today = date.today()
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
            "email": user.email,
            "telefono": user.telefono,
            "edad": user.edad,
            "fecha_nacimiento": str(user.fecha_nacimiento) if user.fecha_nacimiento else None
        }
    }), 200

# --- OCR Verification ---
@main_bp.route('/analyze-document', methods=['POST'])
def analyze_document():
    import base64
    import os
    from openai import OpenAI

    
    if 'file' not in request.files:
        return jsonify({"msg": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400
        
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"msg": "OpenAI API key not configured"}), 500
        
    try:
        client = OpenAI(api_key=api_key)
        
        file_content = file.read()
        image_data = base64.b64encode(file_content).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract 'numero_colegiado' (only digits) and 'nombre_completo' from this accreditation document. Return valid JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ],
                }
            ],
            response_format={ "type": "json_object" }
        )
        
        extracted_data = json.loads(response.choices[0].message.content)
        numero_colegiado = extracted_data.get('numero_colegiado')
        
        from app.adapters.copc_adapter import CopcAdapter
        adapter = CopcAdapter()
        verification_result = adapter.verify(numero_colegiado)
        
        # Combinamos los resultados
        result = {
            "numero_licencia": verification_result.get("numero_colegiado") or numero_colegiado,
            "nombre": verification_result.get("nombre") or extracted_data.get('nombre_completo'),
            "verified": verification_result.get("verified", False),
            "institucion": verification_result.get("institucion") or extracted_data.get('institucion', "Desconocida"),
            "msg": verification_result.get("msg")
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"msg": f"OCR Error: {str(e)}"}), 500



