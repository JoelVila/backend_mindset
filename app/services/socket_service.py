"""
Servicio de WebSockets para el chat en tiempo real de tickets.
Usa Flask-SocketIO. Los clientes se unen a rooms con nombre 'ticket_<id>'.
"""
from flask_socketio import SocketIO, join_room, leave_room, emit
from app import db
from app.models import Ticket, TicketMensaje, Paciente, Psicologo
from datetime import datetime
from app.services.fcm_service import FCMService

socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')


def init_socketio(app):
    """Inicializa SocketIO con la aplicación Flask."""
    socketio.init_app(app, cors_allowed_origins="*")
    return socketio


@socketio.on('connect')
def on_connect():
    print("DEBUG: Cliente conectado vía WebSocket")
    emit('connected', {'msg': 'Conexión WebSocket establecida'})


@socketio.on('disconnect')
def on_disconnect():
    pass


@socketio.on('join_ticket')
def on_join_ticket(data):
    """
    El cliente se une a la sala del ticket para recibir mensajes en tiempo real.
    data: { 'ticket_id': int }
    """
    ticket_id = data.get('ticket_id')
    if not ticket_id:
        emit('error', {'msg': 'ticket_id requerido'})
        return
    room = f'ticket_{ticket_id}'
    join_room(room)
    emit('joined', {'msg': f'Conectado al ticket #{ticket_id}', 'ticket_id': ticket_id})


@socketio.on('leave_ticket')
def on_leave_ticket(data):
    """
    El cliente abandona la sala del ticket.
    data: { 'ticket_id': int }
    """
    ticket_id = data.get('ticket_id')
    if ticket_id:
        room = f'ticket_{ticket_id}'
        leave_room(room)


@socketio.on('send_message')
def on_send_message(data):
    """
    Recibe un mensaje, lo guarda en BD y lo emite a todos en la sala.
    data: {
        'ticket_id': int,
        'mensaje': str,
        'remitente': str (nombre del usuario),
        'tipo_emisor': str ('paciente' | 'psicologo' | 'admin' | 'bot')
    }
    """
    ticket_id = data.get('ticket_id')
    mensaje = data.get('mensaje', '').strip()
    remitente = data.get('remitente', 'Usuario')
    tipo_emisor = data.get('tipo_emisor', 'paciente')

    if not ticket_id or not mensaje:
        emit('error', {'msg': 'ticket_id y mensaje son obligatorios'})
        return

    # 1. Guardar en BD para persistencia
    nuevo_mensaje = TicketMensaje(
        id_ticket=ticket_id,
        mensaje=mensaje,
        remitente=remitente,
        tipo_emisor=tipo_emisor
    )
    db.session.add(nuevo_mensaje)

    # 2. Actualizar estado del ticket si es admin
    if tipo_emisor == 'admin':
        ticket = Ticket.query.get(ticket_id)
        if ticket:
            ticket.respuesta_admin = mensaje
            ticket.estado = 'en_progreso'
    
    db.session.commit()

    # 3. Emitir payload
    room = f'ticket_{ticket_id}'
    payload = {
        'id': nuevo_mensaje.id,
        'ticket_id': ticket_id,
        'mensaje': mensaje,
        'remitente': remitente,
        'tipo_emisor': tipo_emisor,
        'fecha_envio': nuevo_mensaje.fecha_envio.isoformat()
    }
    emit('new_message', payload, room=room)

    # 4. Enviar Notificaci\u00f3n Push (FCM) al destinatario
    try:
        ticket = Ticket.query.get(ticket_id)
        if ticket:
            title_push = f"Nuevo mensaje de {remitente}"
            body_push = mensaje[:100] + "..." if len(mensaje) > 100 else mensaje
            
            # Si el paciente escribe, notificar al psic\u00f3logo
            if tipo_emisor == 'paciente' and ticket.id_psicologo:
                psico = Psicologo.query.get(ticket.id_psicologo)
                if psico and psico.fcm_token:
                    FCMService.send_push(psico.fcm_token, title_push, body_push, data={"type": "chat_message", "ticket_id": str(ticket_id)})
            
            # Si el psic\u00f3logo o admin escribe, notificar al paciente
            elif (tipo_emisor == 'psicologo' or tipo_emisor == 'admin') and ticket.id_paciente:
                pac = Paciente.query.get(ticket.id_paciente)
                if pac and pac.fcm_token:
                    FCMService.send_push(pac.fcm_token, title_push, body_push, data={"type": "chat_message", "ticket_id": str(ticket_id)})
    except Exception as e_push:
        print(f"Error enviando push en chat: {e_push}")
