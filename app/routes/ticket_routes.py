from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Ticket, Paciente, Psicologo, TicketMensaje
from app.errors import APIException
import json

tickets_bp = Blueprint('tickets', __name__)


def _get_identity():
    """Extrae y parsea la identidad del JWT."""
    identity = get_jwt_identity()
    if isinstance(identity, str):
        try:
            identity = json.loads(identity)
        except (json.JSONDecodeError, ValueError):
            pass
    return identity


# ==================== TICKETS ====================

@tickets_bp.route('/tickets', methods=['POST'])
@jwt_required()
def crear_ticket():
    """
    Crear un nuevo ticket de soporte
    ---
    tags:
      - Tickets
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - asunto
            - descripcion
          properties:
            asunto:
              type: string
              example: "Problema con el pago"
            descripcion:
              type: string
              example: "No se procesó correctamente mi pago."
            prioridad:
              type: string
              enum: [baja, media, alta]
              example: "media"
            imagen_adjunta:
              type: string
              description: "Imagen en formato Base64"
    responses:
      201:
        description: Ticket creado correctamente
      400:
        description: Datos inválidos
    """
    identity = _get_identity()
    data = request.get_json()

    if not data:
        raise APIException('No se recibieron datos', 400)

    asunto = data.get('asunto', '').strip()
    descripcion = data.get('descripcion', '').strip()
    prioridad = data.get('prioridad', 'media')
    imagen_adjunta = data.get('imagen_adjunta')

    if not asunto:
        raise APIException('El asunto es obligatorio', 400)
    if not descripcion:
        raise APIException('La descripción es obligatoria', 400)
    if prioridad not in ('baja', 'media', 'alta'):
        raise APIException('Prioridad inválida. Usa: baja, media o alta', 400)

    role = identity.get('role') if isinstance(identity, dict) else None
    user_id = identity.get('id') if isinstance(identity, dict) else None

    id_paciente = user_id if role == 'paciente' else None
    id_psicologo = user_id if role == 'psicologo' else None

    ticket = Ticket(
        id_paciente=id_paciente,
        id_psicologo=id_psicologo,
        asunto=asunto,
        descripcion=descripcion,
        prioridad=prioridad,
        estado='abierto',
        imagen_adjunta=imagen_adjunta
    )
    db.session.add(ticket)
    db.session.commit()

    # --- Lógica del Chatbot ---
    # Creamos dos mensajes automáticos del bot
    msg1 = TicketMensaje(
        id_ticket=ticket.id_ticket,
        mensaje="¡Hola! Soy el asistente automático de MindConnect. 🤖",
        remitente="Asistente MindConnect",
        tipo_emisor="bot"
    )
    msg2 = TicketMensaje(
        id_ticket=ticket.id_ticket,
        mensaje="Para agilizar tu consulta: ¿Es la primera vez que experimentas este inconveniente o ya te había sucedido antes?",
        remitente="Asistente MindConnect",
        tipo_emisor="bot"
    )
    db.session.add(msg1)
    db.session.add(msg2)
    db.session.commit()

    return jsonify({'msg': 'Ticket creado correctamente', 'ticket': ticket.to_dict()}), 201


@tickets_bp.route('/tickets/<int:id_ticket>/mensajes', methods=['GET'])
@jwt_required()
def listar_mensajes_ticket(id_ticket):
    """
    Listar los mensajes de un ticket (historial del chat)
    ---
    tags:
      - Tickets
    security:
      - Bearer: []
    parameters:
      - name: id_ticket
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Lista de mensajes del chat
    """
    identity = _get_identity()
    role = identity.get('role') if isinstance(identity, dict) else None
    user_id = identity.get('id') if isinstance(identity, dict) else None

    ticket = Ticket.query.get(id_ticket)
    if not ticket:
        raise APIException('Ticket no encontrado', 404)

    # Verificar permisos (admin puede ver todos, usuario solo los suyos)
    if role != 'admin':
        if role == 'paciente' and ticket.id_paciente != user_id:
            raise APIException('No tienes permiso para ver este chat', 403)
        if role == 'psicologo' and ticket.id_psicologo != user_id:
            raise APIException('No tienes permiso para ver este chat', 403)

    mensajes = TicketMensaje.query.filter_by(id_ticket=id_ticket).order_by(TicketMensaje.fecha_envio.asc()).all()
    return jsonify([m.to_dict() for m in mensajes]), 200


@tickets_bp.route('/tickets', methods=['GET'])
@jwt_required()
def listar_tickets():
    """
    Listar los tickets del usuario autenticado
    ---
    tags:
      - Tickets
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de tickets del usuario
    """
    identity = _get_identity()
    role = identity.get('role') if isinstance(identity, dict) else None
    user_id = identity.get('id') if isinstance(identity, dict) else None

    if role == 'paciente':
        tickets = Ticket.query.filter_by(id_paciente=user_id).order_by(Ticket.fecha_creacion.desc()).all()
    elif role == 'psicologo':
        tickets = Ticket.query.filter_by(id_psicologo=user_id).order_by(Ticket.fecha_creacion.desc()).all()
    else:
        raise APIException('Rol no reconocido', 403)

    return jsonify([t.to_dict() for t in tickets]), 200


@tickets_bp.route('/tickets/<int:id_ticket>', methods=['GET'])
@jwt_required()
def ver_ticket(id_ticket):
    """
    Ver el detalle de un ticket
    ---
    tags:
      - Tickets
    security:
      - Bearer: []
    parameters:
      - name: id_ticket
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Detalle del ticket
      404:
        description: Ticket no encontrado
    """
    identity = _get_identity()
    role = identity.get('role') if isinstance(identity, dict) else None
    user_id = identity.get('id') if isinstance(identity, dict) else None

    ticket = Ticket.query.get(id_ticket)
    if not ticket:
        raise APIException('Ticket no encontrado', 404)

    # Verificar que el ticket pertenece al usuario
    if role == 'paciente' and ticket.id_paciente != user_id:
        raise APIException('No tienes permiso para ver este ticket', 403)
    if role == 'psicologo' and ticket.id_psicologo != user_id:
        raise APIException('No tienes permiso para ver este ticket', 403)

    return jsonify(ticket.to_dict()), 200


@tickets_bp.route('/tickets/<int:id_ticket>/estado', methods=['PUT'])
@jwt_required()
def actualizar_estado_ticket(id_ticket):
    """
    Actualizar el estado de un ticket (solo admin)
    ---
    tags:
      - Tickets
    security:
      - Bearer: []
    parameters:
      - name: id_ticket
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            estado:
              type: string
              enum: [abierto, en_progreso, cerrado]
            respuesta_admin:
              type: string
    responses:
      200:
        description: Estado actualizado
      403:
        description: Sin permisos
      404:
        description: Ticket no encontrado
    """
    identity = _get_identity()
    role = identity.get('role') if isinstance(identity, dict) else None

    if role != 'admin':
        raise APIException('Solo el administrador puede actualizar el estado', 403)

    ticket = Ticket.query.get(id_ticket)
    if not ticket:
        raise APIException('Ticket no encontrado', 404)

    data = request.get_json() or {}
    nuevo_estado = data.get('estado')
    respuesta = data.get('respuesta_admin')

    if nuevo_estado and nuevo_estado not in ('abierto', 'en_progreso', 'cerrado'):
        raise APIException('Estado inválido', 400)

    if nuevo_estado:
        ticket.estado = nuevo_estado
    if respuesta:
        ticket.respuesta_admin = respuesta

    db.session.commit()
    return jsonify({'msg': 'Ticket actualizado', 'ticket': ticket.to_dict()}), 200


@tickets_bp.route('/tickets/<int:id_ticket>', methods=['DELETE'])
@jwt_required()
def eliminar_ticket(id_ticket):
    """
    Eliminar un ticket específico
    ---
    tags:
      - Tickets
    security:
      - Bearer: []
    parameters:
      - name: id_ticket
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Ticket eliminado correctamente
      403:
        description: No tienes permiso para eliminar este ticket
      404:
        description: Ticket no encontrado
    """
    identity = _get_identity()
    role = identity.get('role') if isinstance(identity, dict) else None
    user_id = identity.get('id') if isinstance(identity, dict) else None

    ticket = Ticket.query.get(id_ticket)
    if not ticket:
        raise APIException('Ticket no encontrado', 404)

    # Verificar permisos (solo el dueño puede borrarlo si no es admin)
    if role != 'admin':
        if role == 'paciente' and ticket.id_paciente != user_id:
            raise APIException('No tienes permiso para eliminar este ticket', 403)
        if role == 'psicologo' and ticket.id_psicologo != user_id:
            raise APIException('No tienes permiso para eliminar este ticket', 403)

    db.session.delete(ticket)
    db.session.commit()
    return jsonify({'msg': 'Ticket eliminado correctamente'}), 200


@tickets_bp.route('/tickets/bulk-delete', methods=['POST'])
@jwt_required()
def eliminar_tickets_masivo():
    """
    Eliminar múltiples tickets
    ---
    tags:
      - Tickets
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            ids:
              type: array
              items:
                type: integer
              example: [1, 2, 3]
    responses:
      200:
        description: Tickets eliminados correctamente
      400:
        description: No se proporcionaron IDs
    """
    identity = _get_identity()
    role = identity.get('role') if isinstance(identity, dict) else None
    user_id = identity.get('id') if isinstance(identity, dict) else None

    data = request.get_json()
    ids = data.get('ids', [])

    if not ids:
        raise APIException('No se proporcionaron IDs de tickets para eliminar', 400)

    # Buscar los tickets
    tickets = Ticket.query.filter(Ticket.id_ticket.in_(ids)).all()
    
    tickets_a_borrar = []
    for t in tickets:
        # Verificar permisos para cada uno
        puedo_borrar = False
        if role == 'admin':
            puedo_borrar = True
        elif role == 'paciente' and t.id_paciente == user_id:
            puedo_borrar = True
        elif role == 'psicologo' and t.id_psicologo == user_id:
            puedo_borrar = True
            
        if puedo_borrar:
            tickets_a_borrar.append(t)

    for t in tickets_a_borrar:
        db.session.delete(t)
    
    db.session.commit()
    return jsonify({'msg': f'{len(tickets_a_borrar)} tickets eliminados correctamente'}), 200
