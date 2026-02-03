import stripe
import os

class PaymentService:
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        # URL base del frontend para redirecciones (ajustar según entorno)
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')

    def create_checkout_session(self, cita_id, concepto, precio_eur, email_paciente):
        """
        Crea una sesión de pago en Stripe.
        Retorna la URL de pago.
        """
        try:
            # Convertir precio a céntimos (Stripe usa enteros)
            precio_cents = int(precio_eur * 100)
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': concepto,
                        },
                        'unit_amount': precio_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                customer_email=email_paciente,
                # Metadata para rastrear qué cita se pagó
                metadata={
                    'cita_id': str(cita_id)
                },
                success_url=f"{self.frontend_url}/pago-exitoso?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{self.frontend_url}/pago-cancelado",
            )
            
            return session.url, session.id
            
        except Exception as e:
            print(f"Error creando sesión de Stripe: {e}")
            return None, None
