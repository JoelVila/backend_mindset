from flask import Blueprint, request, jsonify
from app.adapters.stripe_adapter import StripeAdapter
import os
from app.services.cita_service import CitaService

webhook_bp = Blueprint('webhook', __name__)
stripe_adapter = StripeAdapter()

@webhook_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET') # Debe configurarse en .env

    event = None

    try:
        # Use adapter to construct event
        event = stripe_adapter.construct_event(payload, sig_header, endpoint_secret)
        
        # Fallback for dev if needed (logic encapsulated in adapter or here)
        if not event and not endpoint_secret:
             data = request.json
             event = stripe_adapter.construct_event_dev(data)

    except ValueError as e:
        # Payload inválido
        return 'Invalid payload', 400
    except Exception as e: # Catching generic exception since adapter might raise stripe errors
        # Firma inválida or other stripe error
        return 'Invalid signature or error', 400

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
