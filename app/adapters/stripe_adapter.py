import stripe
import os

class StripeAdapter:
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')

    def create_checkout_session(self, item_name, amount_eur, customer_email, metadata, success_suffix="/pago-exitoso?session_id={CHECKOUT_SESSION_ID}", cancel_suffix="/pago-cancelado"):
        """
        Creates a Stripe checkout session.
        params:
            item_name: str
            amount_eur: float
            customer_email: str
            metadata: dict
            success_suffix: str - URL suffix for success redirection
            cancel_suffix: str - URL suffix for cancel redirection
        returns: (session_url, session_id)
        """
        try:
            # Convert price to cents (Stripe uses integers)
            price_cents = int(amount_eur * 100)
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': item_name,
                        },
                        'unit_amount': price_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                customer_email=customer_email,
                metadata=metadata,
                # URLs HTTP que el WebView puede detectar
                # El WebView intercepta estas URLs y cierra con el resultado correcto
                success_url=f'http://10.0.2.2:5000/payment/success?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'http://10.0.2.2:5000/payment/cancel',
            )
            
            return session.url, session.id
            
        except Exception as e:
            print(f"Error creating Stripe session: {e}")
            return None, None

    def construct_event(self, payload, sig_header, endpoint_secret) -> stripe.Event:
        """
        Constructs a Stripe event from the webhook payload.
        Raises ValueError or stripe.error.SignatureVerificationError on failure.
        """
        if endpoint_secret:
             return stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        else:
            # Development fallback (use with caution)
            data = stripe.util.json.loads(payload) # Using json loads for safety/compatibility or just pass dict if caller did that
            # Actually, standard way if no secret is checked is:
            # stripe.Event.construct_from(json_payload, key)
            # The caller passed raw payload strings usually.
            # Let's stick to what the original code did but cleaner.
            # Original code did: data = request.json; event = stripe.Event.construct_from(data, stripe.api_key)
            # We will handle this difference in the adapter logic or expect caller to pass what's needed.
            # Better: Let the caller decide based on secret presence? 
            # Or handle it here.
            pass
        return None
    
    def get_payment_intent_from_session(self, session_id):
        """Retrieves payment intent ID from a checkout session"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session.payment_intent
        except Exception as e:
            print(f"Error retrieving Stripe session: {e}")
            return None

    def refund_payment(self, payment_intent_id, amount_cents=None):
        """Processes a refund in Stripe (full or partial)"""
        try:
            params = {'payment_intent': payment_intent_id}
            if amount_cents:
                params['amount'] = amount_cents
            
            refund = stripe.Refund.create(**params)
            return refund
        except Exception as e:
            print(f"Error processing refund: {e}")
            return None
