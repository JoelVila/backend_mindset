from flask import Blueprint, request, jsonify, redirect, send_file
import os
from app import db
from app.models import Psicologo, Paciente, Cita, Especialidad, Anamnesis, Informe, Factura, Notificacion, ConsentimientoInformado
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import json
import re
from app.services.psicologo_service import PsicologoService
from app.services.cita_service import CitaService
from app.services.general_service import InformeService, HistorialService, FacturaService, EspecialidadService
from app.services.resena_service import ResenaService
from app.services.email_service import EmailService
from app.utils.pdf_generator import generate_invoice_pdf
from app.adapters.ocr_adapter import OCRAdapter
from app.adapters.copc_adapter import CopcAdapter
from app.adapters.stripe_adapter import StripeAdapter
import stripe
import secrets
import base64
import io

# Initialize email service
email_service = EmailService()

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

# --- Image Serving Routes ---
@main_bp.route('/psicologo/<int:id_psicologo>/foto', methods=['GET'])
def get_psicologo_foto(id_psicologo):
    psicologo = Psicologo.query.get_or_404(id_psicologo)
    if not psicologo.foto_psicologo:
        return jsonify({"msg": "No photo available"}), 404
    
    try:
        data = psicologo.foto_psicologo
        # Si es una URL externa, redirigir
        if data.startswith('http://') or data.startswith('https://'):
            return redirect(data)
        elif data.startswith('data:image'):
            header, encoded = data.split(",", 1)
            mime_type = header.split(";")[0].split(":")[1]
            image_bytes = base64.b64decode(encoded)
            return send_file(io.BytesIO(image_bytes), mimetype=mime_type)
        else:
            # Assume it's just base64 standard
            image_bytes = base64.b64decode(data)
            return send_file(io.BytesIO(image_bytes), mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"msg": f"Error processing image: {str(e)}"}), 500

@main_bp.route('/paciente/<int:id_paciente>/foto', methods=['GET'])
def get_paciente_foto(id_paciente):
    paciente = Paciente.query.get_or_404(id_paciente)
    if not paciente.foto_paciente:
        return jsonify({"msg": "No photo available"}), 404
    
    try:
        data = paciente.foto_paciente
        # Si es una URL externa, redirigir
        if data.startswith('http://') or data.startswith('https://'):
            return redirect(data)
        elif data.startswith('data:image'):
            header, encoded = data.split(",", 1)
            mime_type = header.split(";")[0].split(":")[1]
            image_bytes = base64.b64decode(encoded)
            return send_file(io.BytesIO(image_bytes), mimetype=mime_type)
        else:
            # Assume it's just base64 standard
            image_bytes = base64.b64decode(data)
            return send_file(io.BytesIO(image_bytes), mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"msg": f"Error processing image: {str(e)}"}), 500

@main_bp.route('/cita/<int:id_cita>/documentacion', methods=['GET'])
def get_cita_documentacion(id_cita):
    cita = Cita.query.get_or_404(id_cita)
    if not cita.documentacion_cancelacion:
        return jsonify({"msg": "No documentation available"}), 404
    
    try:
        data = cita.documentacion_cancelacion
        if data.startswith('data:'):
            header, encoded = data.split(",", 1)
            mime_type = header.split(";")[0].split(":")[1]
            image_bytes = base64.b64decode(encoded)
            return io.BytesIO(image_bytes), 200, {'Content-Type': mime_type}
        return io.BytesIO(base64.b64decode(data)), 200, {'Content-Type': 'image/jpeg'}
    except Exception as e:
        return jsonify({"msg": str(e)}), 500



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
        # Get first specialty ID if available (for appointments)
        especialidad_id = p.especialidades[0].id_especialidad if p.especialidades else None
        
        result.append({
            'id_psicologo': p.id_psicologo,
            'nombre': p.nombre,
            'email': p.correo_electronico,
            'telefono': p.telefono,
            'especialidad': esp_nombre,
            'especialidad_id': especialidad_id
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
        # Get first specialty ID if available (for appointments)
        especialidad_id = p.especialidades[0].id_especialidad if p.especialidades else None
        
        # Get rating stats
        rating_stats = ResenaService.get_rating_stats(p.id_psicologo)
        
        result.append({
            'id_psicologo': p.id_psicologo,
            'nombre': p.nombre,
            'foto_perfil': f"/main/psicologo/{p.id_psicologo}/foto" if p.foto_psicologo else None,
            'especialidades': especialidades_list,
            'especialidad_id': especialidad_id,  # Add the specialty ID
            'email': p.correo_electronico,
            'telefono': p.telefono,
            'numero_colegiado': p.numero_colegiado,
            # Campos recuperados
            'bio': p.bio,
            'anios_experiencia': p.anios_experiencia,
            'precio_online': float(p.precio_online) if p.precio_online else None,
            'video_presentacion_url': p.video_presentacion_url,
            'ofrece_sesion_intro': p.ofrece_sesion_intro,
            'precio_sesion_intro': float(p.precio_sesion_intro) if p.precio_sesion_intro else 0.0,
            'valoracion_media': rating_stats['puntuacion_media'],
            'total_resenas': rating_stats['total_resenas']
        })
    
    return jsonify(result), 200



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
                "nombre": psicologo.nombre,
                "telefono": psicologo.telefono
            },
           "motivo": nueva_cita.motivo,
           "motivo_orientativo": nueva_cita.motivo_orientativo,
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
    current_user = get_current_user_helper()
    
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
            "precio_online": float(psicologo.precio_online) if psicologo.precio_online else None,
            "foto_perfil": psicologo.foto_psicologo,
            "bio": psicologo.bio,
            "video_presentacion_url": psicologo.video_presentacion_url,
            "ofrece_sesion_intro": psicologo.ofrece_sesion_intro,
            "precio_sesion_intro": float(psicologo.precio_sesion_intro) if psicologo.precio_sesion_intro else 0.0
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
    current_user = get_current_user_helper()
    
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
        "precio_online": float(psicologo.precio_online) if psicologo.precio_online else None,
        "banco": psicologo.banco,
        "titular_cuenta": psicologo.titular_cuenta,
        # Onboarding
        "onboarding_completado": psicologo.onboarding_completado or False,
        "horario": json.loads(psicologo.horario_json) if psicologo.horario_json else None,
        "max_pacientes_dia": psicologo.max_pacientes_dia,
        "video_presentacion_url": psicologo.video_presentacion_url,
        "ofrece_sesion_intro": psicologo.ofrece_sesion_intro,
        "precio_sesion_intro": float(psicologo.precio_sesion_intro) if psicologo.precio_sesion_intro else 0.0,
        "valoracion": ResenaService.get_rating_stats(psicologo.id_psicologo)
    }), 200


# --- Pagos / Payments ---
@main_bp.route('/pagos/crear-checkout', methods=['POST'])
@jwt_required()
def crear_checkout_pago():
    """
    Create a Stripe checkout session for appointment payment
    ---
    tags:
      - Pagos
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            precio_cita:
              type: number
            id_psicologo:
              type: integer
            fecha:
              type: string
            hora:
              type: string
            tipo_cita:
              type: string
    responses:
      200:
        description: Checkout session created
      400:
        description: Missing required fields
      404:
        description: Patient or psychologist not found
    """
    current_user = get_current_user_helper()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['precio_cita', 'id_psicologo', 'fecha', 'hora', 'tipo_cita']
    for field in required_fields:
        if field not in data:
            return jsonify({"msg": f"Campo requerido: {field}"}), 400
    
    try:
        # Get patient email
        paciente = Paciente.query.get(current_user['id'])
        if not paciente:
            return jsonify({"msg": "Paciente no encontrado"}), 404
        
        # Get psychologist name
        psicologo = Psicologo.query.get(data['id_psicologo'])
        if not psicologo:
            return jsonify({"msg": "Psicólogo no encontrado"}), 404
        
        # --- VALIDACIÓN: LÍMITE SEMANAL ---
        permitido, error_msg = CitaService.verificar_limite_semanal(current_user['id'], data['fecha'])
        if not permitido:
            return jsonify({"msg": error_msg}), 400
        # --- FIN VALIDACIÓN ---
        
        # Create Stripe checkout session
        stripe_adapter = StripeAdapter()
        
        item_name = f"Sesión de psicología con {psicologo.nombre} {psicologo.apellido}"
        amount_eur = float(data['precio_cita'])
        customer_email = paciente.correo_electronico
        
        metadata = {
            'id_paciente': str(current_user['id']),
            'id_psicologo': str(data['id_psicologo']),
            'fecha': data['fecha'],
            'hora': data['hora'],
            'tipo_cita': data.get('tipo_cita', 'videollamada'),
            'id_especialidad': str(data.get('id_especialidad', '')),
            'motivo_orientativo': data.get('motivo_orientativo', '')
        }
        
        # Create checkout session
        session_url, session_id = stripe_adapter.create_checkout_session(
            item_name=item_name,
            amount_eur=amount_eur,
            customer_email=customer_email,
            metadata=metadata
        )
        
        if not session_url:
            return jsonify({"msg": "Error al crear sesión de pago"}), 500
        
        # --- NUEVO: CREAR CITA EN ESTADO PENDIENTE DE PAGO ---
        # Esto asegura que el límite semanal detecte esta cita de inmediato
        try:
            import secrets
            enlace_meet = None
            if data.get('tipo_cita', 'videollamada') == 'videollamada':
                enlace_meet = f"https://meet.jit.si/MindConnect-{secrets.token_urlsafe(10)}"

            nueva_cita = Cita(
                id_paciente=current_user['id'],
                id_psicologo=data['id_psicologo'],
                fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date(),
                hora=datetime.strptime(data['hora'], '%H:%M').time(),
                tipo_cita=data.get('tipo_cita', 'videollamada'),
                precio_cita=amount_eur,
                estado='pendiente_pago',
                stripe_session_id=session_id,
                enlace_meet=enlace_meet,
                id_especialidad=data.get('id_especialidad'),
                motivo_orientativo=data.get('motivo_orientativo')
            )
            db.session.add(nueva_cita)
            db.session.commit()
            print(f"✅ Pre-registrada cita {nueva_cita.id_cita} (pendiente de pago) para sesión {session_id}")
        except Exception as e_cita:
            print(f"⚠️ Error pre-registrando cita: {e_cita}")
            # No bloqueamos el retorno de la URL de pago si falló el registro,
            # pero lo ideal es que no falle.
        
        return jsonify({
            "checkout_url": session_url,
            "session_id": session_id
        }), 200
        
    except Exception as e:
        print(f"Error creating checkout: {e}")
        return jsonify({"msg": f"Error: {str(e)}"}), 500

@main_bp.route('/pagos/reintentar-pago/<int:id_cita>', methods=['POST'])
@jwt_required()
def reintentar_pago_cita(id_cita):
    """
    Generate a new Stripe checkout session for an existing appointment pending payment.
    """
    current_user = get_current_user_helper()
    
    cita = Cita.query.get_or_404(id_cita)
    
    # Verify owner
    if cita.id_paciente != current_user['id']:
        return jsonify({"msg": "No autorizado"}), 403
    
    # Verify status
    if cita.estado != 'pendiente_pago':
        return jsonify({"msg": f"La cita no está en espera de pago (Estado: {cita.estado})"}), 400

    try:
        psicologo = cita.psicologo
        paciente = cita.paciente
        
        # Create Stripe checkout session
        stripe_adapter = StripeAdapter()
        
        item_name = f"Sesión de psicología con {psicologo.nombre} {psicologo.apellido}"
        amount_eur = float(cita.precio_cita)
        customer_email = paciente.correo_electronico
        
        metadata = {
            'id_paciente': str(cita.id_paciente),
            'id_psicologo': str(cita.id_psicologo),
            'fecha': str(cita.fecha),
            'hora': str(cita.hora)[0:5],
            'tipo_cita': cita.tipo_cita,
            'id_especialidad': str(cita.id_especialidad or ''),
            'motivo_orientativo': cita.motivo_orientativo or ''
        }
        
        # Create checkout session
        session_url, session_id = stripe_adapter.create_checkout_session(
            item_name=item_name,
            amount_eur=amount_eur,
            customer_email=customer_email,
            metadata=metadata
        )
        
        if not session_url:
            return jsonify({"msg": "Error al crear sesión de pago"}), 500
        
        # Update it with new session id so webhook works
        cita.stripe_session_id = session_id
        db.session.commit()
        
        return jsonify({
            "checkout_url": session_url,
            "session_id": session_id
        }), 200
        
    except Exception as e:
        print(f"Error recreating checkout: {e}")
        return jsonify({"msg": f"Error: {str(e)}"}), 500

# --- Páginas de resultado de pago (detectadas por el WebView interno) ---
from flask import render_template_string

@main_bp.route('/payment/success', methods=['GET'])
def payment_success_page():
    """
    Página de éxito de pago - detectada por el WebView de la app
    El WebView intercepta esta URL y cierra la pantalla con éxito
    """
    session_id = request.args.get('session_id', '')
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pago Completado</title>
        <style>
            body {{ font-family: Arial, sans-serif; display: flex; justify-content: center;
                   align-items: center; min-height: 100vh; margin: 0; background: #f0fdf4; }}
            .card {{ text-align: center; padding: 40px; background: white;
                    border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); max-width: 320px; }}
            .icon {{ font-size: 64px; margin-bottom: 16px; }}
            h1 {{ color: #10B981; font-size: 24px; margin-bottom: 8px; }}
            p {{ color: #64748B; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">✅</div>
            <h1>¡Pago Exitoso!</h1>
            <p>Tu cita ha sido confirmada.<br>Vuelve a la app para continuar.</p>
        </div>
    </body>
    </html>
    """
    return html, 200

@main_bp.route('/payment/cancel', methods=['GET'])
def payment_cancel_page():
    """
    Página de cancelación de pago - detectada por el WebView de la app
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pago Cancelado</title>
        <style>
            body { font-family: Arial, sans-serif; display: flex; justify-content: center;
                   align-items: center; min-height: 100vh; margin: 0; background: #fff7ed; }
            .card { text-align: center; padding: 40px; background: white;
                    border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); max-width: 320px; }
            .icon { font-size: 64px; margin-bottom: 16px; }
            h1 { color: #F59E0B; font-size: 24px; margin-bottom: 8px; }
            p { color: #64748B; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">❌</div>
            <h1>Pago Cancelado</h1>
            <p>El pago fue cancelado.<br>Vuelve a la app para intentarlo de nuevo.</p>
        </div>
    </body>
    </html>
    """
    return html, 200



# --- Password Reset ---
@main_bp.route('/forgot-password/paciente', methods=['POST'])
def forgot_password_paciente():
    """Request password reset for patient"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"msg": "Email requerido"}), 400
    
    try:
        paciente = Paciente.query.filter_by(correo_electronico=email).first()
        
        if not paciente:
            # Don't reveal if email exists or not (security)
            return jsonify({"msg": "Si el correo existe, recibirás un email con instrucciones"}), 200
        
        # Generate reset token
        token = email_service.generate_reset_token()
        paciente.reset_token = token
        paciente.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        
        db.session.commit()
        
        # Send email
        email_sent = email_service.send_password_reset_email(email, token, 'paciente')
        
        if email_sent:
            return jsonify({"msg": "Si el correo existe, recibirás un email con instrucciones"}), 200
        else:
            return jsonify({"msg": "Error al enviar el correo"}), 500
            
    except Exception as e:
        print(f"Error in forgot password: {e}")
        return jsonify({"msg": "Error al procesar solicitud"}), 500

@main_bp.route('/forgot-password/psicologo', methods=['POST'])
def forgot_password_psicologo():
    """Request password reset for psychologist"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"msg": "Email requerido"}), 400
    
    try:
        psicologo = Psicologo.query.filter_by(correo_electronico=email).first()
        
        if not psicologo:
            return jsonify({"msg": "Si el correo existe, recibirás un email con instrucciones"}), 200
        
        # Generate reset token
        token = email_service.generate_reset_token()
        psicologo.reset_token = token
        psicologo.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        
        db.session.commit()
        
        # Send email
        email_sent = email_service.send_password_reset_email(email, token, 'psicologo')
        
        if email_sent:
            return jsonify({"msg": "Si el correo existe, recibirás un email con instrucciones"}), 200
        else:
            return jsonify({"msg": "Error al enviar el correo"}), 500
            
    except Exception as e:
        print(f"Error in forgot password: {e}")
        return jsonify({"msg": "Error al procesar solicitud"}), 500

@main_bp.route('/reset-password/paciente', methods=['POST'])
def reset_password_paciente():
    """Reset password for patient with token"""
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({"msg": "Token y nueva contraseña requeridos"}), 400
    
    if len(new_password) < 6:
        return jsonify({"msg": "La contraseña debe tener al menos 6 caracteres"}), 400
    
    try:
        # Find patient with valid token
        paciente = Paciente.query.filter_by(reset_token=token).first()
        
        if not paciente:
            return jsonify({"msg": "Token inválido"}), 400
        
        # Check if token expired
        if paciente.reset_token_expiry < datetime.utcnow():
            return jsonify({"msg": "Token expirado"}), 400
        
        # Update password
        paciente.contrasena_hash = generate_password_hash(new_password)
        paciente.reset_token = None
        paciente.reset_token_expiry = None
        
        db.session.commit()
        
        return jsonify({"msg": "Contraseña actualizada exitosamente"}), 200
        
    except Exception as e:
        print(f"Error resetting password: {e}")
        db.session.rollback()
        return jsonify({"msg": "Error al restablecer contraseña"}), 500

@main_bp.route('/reset-password/psicologo', methods=['POST'])
def reset_password_psicologo():
    """Reset password for psychologist with token"""
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({"msg": "Token y nueva contraseña requeridos"}), 400
    
    if len(new_password) < 6:
        return jsonify({"msg": "La contraseña debe tener al menos 6 caracteres"}), 400
    
    try:
        # Find psychologist with valid token
        psicologo = Psicologo.query.filter_by(reset_token=token).first()
        
        if not psicologo:
            return jsonify({"msg": "Token inválido"}), 400
        
        # Check if token expired
        if psicologo.reset_token_expiry < datetime.utcnow():
            return jsonify({"msg": "Token expirado"}), 400
        
        # Update password
        psicologo.contrasena_hash = generate_password_hash(new_password)
        psicologo.reset_token = None
        psicologo.reset_token_expiry = None
        
        db.session.commit()
        
        return jsonify({"msg": "Contraseña actualizada exitosamente"}), 200
        
    except Exception as e:
        print(f"Error resetting password: {e}")
        db.session.rollback()
        return jsonify({"msg": "Error al restablecer contraseña"}), 500

@main_bp.route('/pagos/webhook', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        if endpoint_secret:
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, endpoint_secret
                )
            except ValueError as e:
                # Invalid payload
                return jsonify({"error": "Invalid payload"}), 400
            except stripe.error.SignatureVerificationError as e:
                # Invalid signature
                return jsonify({"error": "Invalid signature"}), 400
        else:
            # Fallback for development (allow only if strictly specified)
            if os.environ.get('FLASK_ENV') == 'development':
                event = stripe.Event.construct_from(
                    request.json, stripe.api_key
                )
            else:
                return jsonify({"error": "Webhook secret not configured"}), 500
        
        print(f"📨 Webhook received: {event['type']}")
        
        # Handle successful payment
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            metadata = session.get('metadata', {})
            
            print(f"✅ Payment successful! Metadata: {metadata}")
            
            # Create appointment from metadata
            try:
                # Generate video link if it's a video call
                tipo_cita = metadata.get('tipo_cita', 'videollamada')
                enlace_meet = None
                if tipo_cita == 'videollamada':
                    # Generar un enlace único de Jitsi Meet (jmeet)
                    enlace_meet = f"https://meet.jit.si/MindConnect-{secrets.token_urlsafe(10)}"

                def safe_int_wh(val):
                    try:
                        return int(val) if val and str(val).strip() else None
                    except (ValueError, TypeError):
                        return None

                nueva_cita = Cita(
                    id_paciente=safe_int_wh(metadata.get('id_paciente')),
                    id_psicologo=safe_int_wh(metadata.get('id_psicologo')),
                    fecha=datetime.strptime(metadata.get('fecha'), '%Y-%m-%d').date(),
                    hora=datetime.strptime(metadata.get('hora'), '%H:%M').time(),
                    tipo_cita=tipo_cita,
                    precio_cita=session.get('amount_total', 0) / 100,  # Convert from cents
                    estado='confirmada',  # Payment confirmed
                    es_primera_vez=True,
                    id_especialidad=safe_int_wh(metadata.get('id_especialidad')),
                    motivo_orientativo=metadata.get('motivo_orientativo'),
                    stripe_session_id=session.get('id'),
                    enlace_meet=enlace_meet
                )
                
                db.session.add(nueva_cita)
                db.session.commit()
                
                # Create Factura automatically
                try:
                    import time
                    factura_data = {
                        'id_paciente': nueva_cita.id_paciente,
                        'id_psicologo': nueva_cita.id_psicologo,
                        'id_cita': nueva_cita.id_cita,
                        'importe_total': float(nueva_cita.precio_cita),
                        'base_imponible': float(nueva_cita.precio_cita),
                        'iva': 0,
                        'concepto': f"Sesion de Psicologia - {nueva_cita.tipo_cita.capitalize()} - {nueva_cita.fecha}",
                        'numero_factura': f"INV-{int(time.time())}-{nueva_cita.id_cita}"
                    }
                    new_factura = FacturaService.create_factura(factura_data)
                    print(f"📄 Factura creada automáticamente via webhook para cita {nueva_cita.id_cita}")

                    # --- ENVIAR FACTURA POR EMAIL ---
                    try:
                        paciente = Paciente.query.get(nueva_cita.id_paciente)
                        psicologo = Psicologo.query.get(nueva_cita.id_psicologo)
                        
                        pdf_bytes = generate_invoice_pdf(paciente, psicologo, new_factura)
                        if pdf_bytes:
                            email_service = EmailService()
                            email_service.send_invoice_email(
                                email=paciente.correo_electronico,
                                invoice_details={
                                    'numero_factura': new_factura.numero_factura,
                                    'concepto': new_factura.concepto,
                                    'total': float(new_factura.importe_total)
                                },
                                pdf_bytes=pdf_bytes,
                                pdf_filename=f"Factura_{new_factura.numero_factura}.pdf"
                            )
                            print(f"📧 Factura enviada por email via webhook a {paciente.correo_electronico}")
                    except Exception as e_mail:
                        print(f"Error sending invoice email via webhook: {e_mail}")

                except Exception as e_fact:
                    print(f"Error creating automatic invoice: {e_fact}")
                
                print(f"✅ Cita creada: ID {nueva_cita.id_cita}")
                
            except Exception as e:
                print(f"❌ Error creating appointment: {e}")
                db.session.rollback()
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 400

@main_bp.route('/pagos/verificar-y-crear', methods=['POST'])
@jwt_required()
def verificar_pago_y_crear_cita():
    """
    Verify Stripe payment and create appointment
    """
    current_user = get_current_user_helper()
    data = request.get_json()
    
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({"msg": "session_id requerido"}), 400
    
    try:
        # Initialize Stripe
        stripe_adapter = StripeAdapter()
        
        # Retrieve session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Check if payment was successful
        if session.payment_status != 'paid':
            return jsonify({"msg": "Pago no completado"}), 400
        
        # 4. Verificar si ya existe registro de esta sesión
        existing_cita = Cita.query.filter_by(stripe_session_id=session_id).first()
        
        # 4. Crear cita si no existía (Fallback) o Confirmar si ya existía
        if existing_cita:
            if existing_cita.estado == 'confirmada':
                return jsonify({
                    "msg": "Cita ya confirmada",
                    "cita_id": existing_cita.id_cita
                }), 200
            else:
                success = CitaService.confirmar_pago(session_id)
                if success:
                    return jsonify({
                        "msg": "Cita confirmada exitosamente",
                        "cita_id": existing_cita.id_cita
                    }), 200
                else:
                    return jsonify({"msg": "Error al confirmar la cita existente"}), 500
        else:
            # Fallback flow: Crear registro si por algún motivo no se creó en el paso anterior
            metadata = session.metadata
            tipo_cita = metadata.get('tipo_cita', 'videollamada')
            enlace_meet = None
            if tipo_cita == 'videollamada':
                import secrets
                enlace_meet = f"https://meet.jit.si/MindConnect-{secrets.token_urlsafe(10)}"

            def safe_int(val):
                try: return int(val) if val and str(val).strip() else None
                except: return None

            id_paciente = safe_int(metadata.get('id_paciente'))
            
            # Validación límite semanal en el fallback también
            permitido, error_msg = CitaService.verificar_limite_semanal(id_paciente, metadata.get('fecha'))
            if not permitido:
                return jsonify({"msg": error_msg}), 400

            nueva_cita = Cita(
                id_paciente=id_paciente,
                id_psicologo=safe_int(metadata.get('id_psicologo')),
                fecha=datetime.strptime(metadata.get('fecha'), '%Y-%m-%d').date(),
                hora=datetime.strptime(metadata.get('hora'), '%H:%M').time(),
                tipo_cita=tipo_cita,
                precio_cita=session.amount_total / 100,
                estado='confirmada',
                id_especialidad=safe_int(metadata.get('id_especialidad')),
                motivo_orientativo=metadata.get('motivo_orientativo'),
                stripe_session_id=session_id,
                enlace_meet=enlace_meet
            )
            db.session.add(nueva_cita)
            db.session.commit()
            
            # Disparar emails/facturas para el nuevo registro
            CitaService.confirmar_pago(session_id)

            return jsonify({
                "msg": "Cita creada y confirmada exitosamente",
                "cita_id": nueva_cita.id_cita
            }), 201
            
    except Exception as e:
        print(f"Error verifying payment: {e}")
        db.session.rollback()
        return jsonify({"msg": f"Error interno: {str(e)}"}), 500

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
    current_user = get_current_user_helper()
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
            'psicologo_telefono': c.psicologo.telefono,
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
    current_user = get_current_user_helper()
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
    current_user = get_current_user_helper()
    
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
                'telefono': paciente.telefono,
                'foto_perfil': f"/main/paciente/{paciente.id_paciente}/foto" if paciente.foto_paciente else None
            },
            'motivo': cita.motivo,
            'motivo_orientativo': cita.motivo_orientativo,
            'enlace_meet': cita.enlace_meet,
            'motivo_cancelacion': cita.motivo_cancelacion,
            'documentacion_cancelacion': f"/main/cita/{cita.id_cita}/documentacion" if cita.documentacion_cancelacion else None,
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
    current_user = get_current_user_helper()
    
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
            'enlace_meet': cita.enlace_meet,
            'psicologo': {
                'id': psicologo.id_psicologo,
                'nombre': psicologo.nombre,
                'foto_perfil': f"/main/psicologo/{psicologo.id_psicologo}/foto" if psicologo.foto_psicologo else None,
                'email': psicologo.correo_electronico,
                'telefono': psicologo.telefono,
                'especialidades': [esp.nombre for esp in psicologo.especialidades],
                'valoracion_media': ResenaService.get_rating_stats(psicologo.id_psicologo)['puntuacion_media'],
                'total_resenas': ResenaService.get_rating_stats(psicologo.id_psicologo)['total_resenas']
            },
            'motivo': cita.motivo,
            'motivo_cancelacion': cita.motivo_cancelacion,
            'documentacion_cancelacion': f"/main/cita/{cita.id_cita}/documentacion" if cita.documentacion_cancelacion else None,
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
    current_user = get_current_user_helper()
        
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
    current_user = get_current_user_helper()
    
    if not isinstance(current_user, dict) or current_user.get('role') != 'psicologo':
        return jsonify({"msg": "Acceso denegado - Solo psicólogos"}), 403
    
    informes = InformeService.get_informes_psicologo(current_user['id'])
    
    result = []
    for informe in informes:
        paciente = informe.paciente
        result.append({
            'id_informe': informe.id_informe,
            'id_cita': informe.id_cita,  # Added for frontend matching
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
    current_user = get_current_user_helper()

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
    current_user = get_current_user_helper()
    
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
    current_user = get_current_user_helper()

    if not isinstance(current_user, dict) or current_user.get('role') != 'psicologo':
        return jsonify({"msg": "Solo psicólogos pueden crear facturas"}), 403

    # Inject psychologist ID from token
    data['id_psicologo'] = current_user['id']
    
    new_factura = FacturaService.create_factura(data)
    return jsonify({"msg": "Factura created", "id": new_factura.id_factura}), 201

# --- Invoice PDF Download ---
import io
from flask import send_file

@main_bp.route('/facturas/<int:id_factura>/pdf', methods=['GET'])
def descargar_factura_pdf(id_factura):
    """
    Descargar PDF de una factura. 
    Soporta id_factura e id_cita (para compatibilidad con frontend).
    """
    # 1. Intentar buscar por ID de Factura
    factura = Factura.query.get(id_factura)
    
    # 2. Si no se encuentra, el frontend podría estar enviando el ID de la Cita
    if not factura:
        factura = Factura.query.filter_by(id_cita=id_factura).first()
    
    # 3. Si sigue sin existir, pero la cita existe y fue pagada/procesada, la creamos al vuelo
    if not factura:
        cita = Cita.query.get(id_factura)
        if cita and cita.precio_cita and cita.precio_cita > 0:
            try:
                from app.services.general_service import FacturaService
                import time
                
                # Generar número de factura coincidente con el formato del frontend si es posible
                # Frontend usa: INV-YYYY-ID (con padding)
                # O simplemente usamos el generador estándar
                factura_data = {
                    'id_paciente': cita.id_paciente,
                    'id_psicologo': cita.id_psicologo,
                    'id_cita': cita.id_cita,
                    'importe_total': float(cita.precio_cita),
                    'base_imponible': float(cita.precio_cita),
                    'iva': 0,
                    'concepto': f"Sesion de Psicologia - {cita.tipo_cita.capitalize()} - {cita.fecha}",
                    'numero_factura': f"INV-{cita.fecha.year}-{str(cita.id_cita).zfill(3)}"
                }
                factura = FacturaService.create_factura(factura_data)
                print(f"✨ Autofix: Factura creada al vuelo para cita {cita.id_cita}")
            except Exception as e:
                print(f"Error en autofix factura: {e}")
                return jsonify({"msg": "Factura no encontrada y no pudo ser generada"}), 404
        else:
            return jsonify({"msg": "Factura no encontrada"}), 404
    
    paciente = Paciente.query.get(factura.id_paciente)
    psicologo = Psicologo.query.get(factura.id_psicologo)
    
    if not paciente or not psicologo:
        return jsonify({"msg": "Datos de paciente o psicólogo no encontrados"}), 404

    try:
        pdf_bytes = generate_invoice_pdf(paciente, psicologo, factura)
        if not pdf_bytes:
            return jsonify({"msg": "Error al generar el PDF"}), 500
            
        return send_file(
            io.BytesIO(pdf_bytes),
            as_attachment=True,
            download_name=f"Factura_{factura.numero_factura}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        print(f"Error en descargar_factura_pdf: {e}")
        return jsonify({"msg": "Error interno del servidor"}), 500

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
        description: Lista de notificaciones
    """
    current_user = get_current_user_helper()
    
    if current_user.get('role') == 'paciente':
        notificaciones = Notificacion.query.filter_by(id_paciente=current_user['id']).order_by(Notificacion.fecha_envio.desc()).all()
    elif current_user.get('role') == 'psicologo':
        notificaciones = Notificacion.query.filter_by(id_psicologo=current_user['id']).order_by(Notificacion.fecha_envio.desc()).all()
    else:
        return jsonify([]), 200

    result = []
    for n in notificaciones:
        result.append({
            'id_notificacion': n.id_notificacion,
            'mensaje': n.mensaje,
            'leida': n.leido,
            'fecha_envio': n.fecha_envio.strftime('%Y-%m-%d %H:%M:%S'),
            'id_cita': n.id_cita
        })
    return jsonify(result), 200

@main_bp.route('/notificaciones/<int:id_notificacion>/leida', methods=['PUT'])
@jwt_required()
def marcar_notificacion_leida(id_notificacion):
    """
    Marcar notificación como leída
    """
    current_user = get_current_user_helper()
    notificacion = Notificacion.query.get(id_notificacion)
    
    if not notificacion:
        return jsonify({"msg": "Notificación no encontrada"}), 404
        
    # Verificar propiedad
    if current_user.get('role') == 'paciente' and notificacion.id_paciente != current_user['id']:
        return jsonify({"msg": "No autorizado"}), 403
    if current_user.get('role') == 'psicologo' and notificacion.id_psicologo != current_user['id']:
        return jsonify({"msg": "No autorizado"}), 403
        
    notificacion.leido = True
    db.session.commit()
    
    return jsonify({"msg": "Notificación marcada como leída"}), 200

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
    print(f"DEBUG: register_paciente initiated for email: {data.get('email')}")
    
    try:
        # Validar campos obligatorios
        required_fields = ['nombre', 'apellido', 'email', 'password', 'telefono', 'dni_nif', 'fecha_nacimiento']
        for field in required_fields:
            if field not in data or not data.get(field):
                print(f"DEBUG: Faltando campo obligatorio: {field}")
                return jsonify({"msg": f"El campo {field} es obligatorio"}), 400

        if Paciente.query.filter_by(correo_electronico=data.get('email')).first():
                print(f"DEBUG: Email ya existe: {data.get('email')}")
                return jsonify({"msg": "Este email ya está registrado"}), 400
                
        fecha_nacim_str = data.get('fecha_nacimiento')
        fecha_nacim = None
        edad = None
        
        try:
            fecha_nacim = datetime.strptime(fecha_nacim_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            edad = today.year - fecha_nacim.year - ((today.month, today.day) < (fecha_nacim.month, fecha_nacim.day))
        except ValueError:
            return jsonify({"msg": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400

        dni_nif = data.get('dni_nif')
        foto_dni = data.get('foto_dni')

        # OCR Extraction in backend if image provided
        if foto_dni and 'base64,' in foto_dni:
            try:
                # Decode image
                header, content = foto_dni.split('base64,')
                image_bytes = base64.b64decode(content)
                
                # Use OCR Adapter
                ocr_adapter = OCRAdapter()
                results = ocr_adapter.extract_text(image_bytes)
                full_text = " ".join(results).upper()
                
                # Look for DNI (8 digits + 1 letter) or NIE (1 letter + 7 digits + 1 letter)
                dni_pattern = r'\b(\d{8}[A-Z]|[XYZ]\d{7}[A-Z])\b'
                dni_matches = re.findall(dni_pattern, full_text)
                
                if dni_matches and (not dni_nif or len(dni_nif) < 5):
                    dni_nif = dni_matches[0]
                    print(f"OCR Backend extracted DNI: {dni_nif}")
            except Exception as ocr_err:
                print(f"Error in backend OCR: {ocr_err}")

        new_user = Paciente(
            nombre=data.get('nombre'),
            correo_electronico=data.get('email'),
            contrasena_hash=generate_password_hash(data.get('password')),
            apellido=data.get('apellido'),
            telefono=data.get('telefono'),
            dni_nif=dni_nif,
            foto_paciente=data.get('foto_perfil'),
            fecha_nacimiento=fecha_nacim,
            edad=edad
        )
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"msg": "Paciente created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"CRITICAL ERROR in register_paciente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Error interno del servidor", "error": str(e)}), 500

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
        identity_str = json.dumps({'id': user.id_paciente, 'role': 'paciente'})
        access_token = create_access_token(identity=identity_str)
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
    current_user = get_current_user_helper()
        
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
            "foto_perfil": user.foto_paciente,
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

# =====================================================
# ONBOARDING PSICÓLOGO (Horario + Máx Pacientes)
# =====================================================

@main_bp.route('/psicologos/onboarding', methods=['POST'])
@jwt_required()
def guardar_onboarding_psicologo():
    """Guarda horario y máx pacientes del psicólogo (onboarding obligatorio)."""
    try:
        current_user = get_current_user_helper()
        psicologo = Psicologo.query.get(current_user['id'])
        if not psicologo:
            return jsonify({"msg": "Psicólogo no encontrado"}), 404

        data = request.get_json()
        horario = data.get('horario')
        max_pacientes = data.get('max_pacientes_dia')

        if not horario or not max_pacientes:
            return jsonify({"msg": "Horario y máximo de pacientes son obligatorios"}), 400

        # Validar max 8h por día
        dias_validos = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
        for dia in dias_validos:
            config = horario.get(dia)
            if config and config.get('activo'):
                inicio = datetime.strptime(config['inicio'], '%H:%M')
                fin = datetime.strptime(config['fin'], '%H:%M')
                horas = (fin - inicio).seconds / 3600
                if horas > 8:
                    return jsonify({"msg": f"El horario de {dia} excede las 8 horas máximas"}), 400

        psicologo.horario_json = json.dumps(horario)
        psicologo.max_pacientes_dia = int(max_pacientes)
        psicologo.onboarding_completado = True
        db.session.commit()

        return jsonify({"msg": "Configuración guardada correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 500

@main_bp.route('/psicologos/<int:id_psicologo>/disponibilidad', methods=['GET'])
def obtener_disponibilidad_psicologo(id_psicologo):
    """Devuelve los slots disponibles para un psicólogo en una fecha dada."""
    try:
        fecha_str = request.args.get('fecha')
        if not fecha_str:
            return jsonify({"msg": "Parámetro 'fecha' es requerido"}), 400

        psicologo = Psicologo.query.get(id_psicologo)
        if not psicologo:
            return jsonify({"msg": "Psicólogo no encontrado"}), 404

        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

        # Mapear weekday() a nombre de día
        dias_map = {0: 'lunes', 1: 'martes', 2: 'miercoles', 3: 'jueves', 4: 'viernes', 5: 'sabado', 6: 'domingo'}
        dia_nombre = dias_map.get(fecha.weekday())

        # Obtener horario del psicólogo
        horario = {}
        if psicologo.horario_json:
            horario = json.loads(psicologo.horario_json)

        config_dia = horario.get(dia_nombre)

        # Si no tiene horario configurado o el día no está activo
        if not config_dia or not config_dia.get('activo'):
            return jsonify({
                "disponible": False,
                "dia_laborable": False,
                "slots": [],
                "max_pacientes_dia": psicologo.max_pacientes_dia or 8
            }), 200

        # Generar slots de 1 hora dentro del rango
        inicio = datetime.strptime(config_dia['inicio'], '%H:%M')
        fin = datetime.strptime(config_dia['fin'], '%H:%M')
        slots = []
        hora_actual = inicio
        while hora_actual < fin:
            slots.append(hora_actual.strftime('%H:%M'))
            hora_actual += timedelta(hours=1)

        # Contar citas ya agendadas para esa fecha
        citas_dia = Cita.query.filter(
            Cita.id_psicologo == id_psicologo,
            Cita.fecha == fecha,
            Cita.estado.in_(['pendiente', 'confirmada', 'programada', 'en_curso', 'pendiente_pago'])
        ).all()

        horas_ocupadas = [c.hora.strftime('%H:%M') for c in citas_dia]
        slots_disponibles = [s for s in slots if s not in horas_ocupadas]

        # Verificar máximo de pacientes
        max_p = psicologo.max_pacientes_dia or 8
        dia_lleno = len(citas_dia) >= max_p

        return jsonify({
            "disponible": not dia_lleno and len(slots_disponibles) > 0,
            "dia_laborable": True,
            "slots": [] if dia_lleno else slots_disponibles,
            "horas_ocupadas": horas_ocupadas,
            "total_citas_dia": len(citas_dia),
            "max_pacientes_dia": max_p,
            "horario": {"inicio": config_dia['inicio'], "fin": config_dia['fin']}
        }), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

# =====================================================
# CONSENTIMIENTO INFORMADO
# =====================================================

@main_bp.route('/consentimiento/check', methods=['GET'])
@jwt_required()
def check_consentimiento():
    """Verifica si el paciente ya firmó el consentimiento con un psicólogo."""
    try:
        current_user = get_current_user_helper()
        id_psicologo = request.args.get('id_psicologo', type=int)
        if not id_psicologo:
            return jsonify({"msg": "id_psicologo es requerido"}), 400

        consentimiento = ConsentimientoInformado.query.filter_by(
            id_paciente=current_user['id'],
            id_psicologo=id_psicologo
        ).first()

        return jsonify({
            "tiene_consentimiento": consentimiento is not None,
            "fecha_aceptacion": consentimiento.fecha_aceptacion.isoformat() if consentimiento else None,
            "version": consentimiento.version_documento if consentimiento else None
        }), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@main_bp.route('/consentimiento/aceptar', methods=['POST'])
@jwt_required()
def aceptar_consentimiento():
    """Registra la aceptación del consentimiento informado."""
    try:
        current_user = get_current_user_helper()
        data = request.get_json()
        id_psicologo = data.get('id_psicologo')

        if not id_psicologo:
            return jsonify({"msg": "id_psicologo es requerido"}), 400

        # Verificar si ya existe
        existente = ConsentimientoInformado.query.filter_by(
            id_paciente=current_user['id'],
            id_psicologo=id_psicologo
        ).first()

        if existente:
            return jsonify({"msg": "Ya has aceptado el consentimiento con este profesional", "ya_aceptado": True}), 200

        nuevo = ConsentimientoInformado(
            id_paciente=current_user['id'],
            id_psicologo=id_psicologo,
            fecha_aceptacion=datetime.utcnow(),
            ip_address=request.remote_addr,
            version_documento='1.0'
        )
        db.session.add(nuevo)
        db.session.commit()

        return jsonify({
            "msg": "Consentimiento registrado correctamente",
            "fecha_aceptacion": nuevo.fecha_aceptacion.isoformat()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 500

@main_bp.route('/consentimiento/pdf', methods=['GET'])
@jwt_required()
def descargar_consentimiento_pdf():
    """Genera y descarga el consentimiento informado en PDF."""
    from flask import send_file
    from app.utils.pdf_generator import generate_consent_pdf
    import io

    try:
        current_user = get_current_user_helper()
        id_psicologo = request.args.get('id_psicologo', type=int)
        if not id_psicologo:
            return jsonify({"msg": "id_psicologo es requerido"}), 400

        consentimiento = ConsentimientoInformado.query.filter_by(
            id_paciente=current_user['id'],
            id_psicologo=id_psicologo
        ).first()

        if not consentimiento:
            return jsonify({"msg": "No se encontró consentimiento firmado"}), 404

        paciente = Paciente.query.get(current_user['id'])
        psicologo = Psicologo.query.get(id_psicologo)

        pdf_bytes = generate_consent_pdf(paciente, psicologo, consentimiento)
        if not pdf_bytes:
            return jsonify({"msg": "Error generando PDF"}), 500

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'consentimiento_{paciente.nombre}_{psicologo.nombre}.pdf'
        )
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

# --- Reseñas / Reviews ---
@main_bp.route('/resenas', methods=['POST'])
@jwt_required()
def create_or_update_resena():
    """
    Enviar o actualizar una reseña (Pacientes)
    ---
    tags:
      - Reseñas
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
            puntuacion:
              type: integer
              description: 1 a 5
            comentario:
              type: string
    responses:
      200:
        description: Reseña guardada
      403:
        description: No elegible (sin citas completadas)
    """
    current_user = get_current_user_helper()
    if current_user.get('role') != 'paciente':
        return jsonify({"msg": "Solo pacientes pueden dejar reseñas"}), 403
    
    resena, error, status = ResenaService.create_or_update_resena(current_user['id'], request.get_json())
    if error:
        return jsonify(error), status
    
    return jsonify({
        "msg": "Reseña guardada exitosamente",
        "resena": {
            "puntuacion": resena.puntuacion,
            "comentario": resena.comentario,
            "fecha": resena.fecha_creacion.isoformat()
        }
    }), 200

@main_bp.route('/psicologos/<int:id_psicologo>/resenas', methods=['GET'])
def get_resenas_psicologo(id_psicologo):
    """
    Obtener reseñas de un psicólogo con ordenación
    ---
    tags:
      - Reseñas
    parameters:
      - name: sort_by
        in: query
        type: string
        enum: [newest, rating_desc, rating_asc]
    responses:
      200:
        description: Lista de reseñas
    """
    sort_by = request.args.get('sort_by', 'newest')
    resenas = ResenaService.get_resenas_psicologo(id_psicologo, sort_by)
    
    result = []
    for r in resenas:
        result.append({
            "id": r.id_resena,
            "puntuacion": r.puntuacion,
            "comentario": r.comentario,
            "fecha": r.fecha_creacion.isoformat(),
            "paciente_nombre": f"{r.paciente_obj.nombre} {r.paciente_obj.apellido[0]}." # Privacidad: Juan P.
        })
    
    stats = ResenaService.get_rating_stats(id_psicologo)
    
    return jsonify({
        "resenas": result,
        "estadisticas": stats
    }), 200

