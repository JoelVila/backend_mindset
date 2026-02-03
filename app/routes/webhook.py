from flask import Blueprint, request, jsonify
import stripe
import os
from app.services.cita_service import CitaService

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET') # Debe configurarse en .env

    event = None

    try:
        # Si tenemos secreto configurado, verificamos firma
        if endpoint_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        else:
            # En desarrollo local sin CLI, a veces confiamos en el payload (NO RECOMENDADO EN PROD)
            # Para test: stripe.Event.construct_from(...)
            data = request.json
            event = stripe.Event.construct_from(data, stripe.api_key)

    except ValueError as e:
        # Payload inválido
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Firma inválida
        return 'Invalid signature', 400

    # Manejar el evento
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Obtener session_id
        session_id = session.get('id')
        print(f"🔔 Webhook recibido: Pago completado para sesión {session_id}")
        
        # Confirmar la cita
        success = CitaService.confirmar_pago(session_id)
        
        if success:
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'msg': 'Cita not found'}), 404

    return jsonify({'status': 'ignored'}), 200
