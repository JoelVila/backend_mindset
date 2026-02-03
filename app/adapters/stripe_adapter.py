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
                success_url=f"{self.frontend_url}{success_suffix}",
                cancel_url=f"{self.frontend_url}{cancel_suffix}",
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
    
    def construct_event_dev(self, data_dict):
        """Helper for dev environment without webhook secret verification"""
        return stripe.Event.construct_from(data_dict, stripe.api_key)
