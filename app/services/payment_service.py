from app.adapters.stripe_adapter import StripeAdapter

class PaymentService:
    def __init__(self):
        self.stripe_adapter = StripeAdapter()

    def create_checkout_session(self, cita_id, concepto, precio_eur, email_paciente):
        """
        Crea una sesión de pago en Stripe.
        Retorna la URL de pago.
        """
        return self.stripe_adapter.create_checkout_session(
            item_name=concepto,
            amount_eur=precio_eur,
            customer_email=email_paciente,
            metadata={'cita_id': str(cita_id)}
        )

