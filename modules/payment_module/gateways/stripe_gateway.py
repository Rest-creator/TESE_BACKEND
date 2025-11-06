import stripe
from django.conf import settings

class StripeGateway:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY  # store in .env
        
        print("Stripe API Key:", stripe.api_key)  # Debugging line to check if the key is loaded correctly

    def charge(self, amount: float, currency: str, source: str) -> dict:
        """
        Charge a card using Stripe.
        amount: in decimal (e.g., 10.50)
        currency: e.g., "usd"
        source: stripe token (from frontend)
        """
        try:
            # Stripe expects amount in cents
            amount_cents = int(amount * 100)
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                payment_method=source,
                confirm=True,
                automatic_payment_methods={
        "enabled": True,
        "allow_redirects": "never"
    }
            )
            
            if payment_intent.status == 'succeeded':
                return {"success": True, "transaction_ref": payment_intent.id}
            else:
                return {"success": False, "transaction_ref": payment_intent.id}

        except stripe.error.CardError as e:
            return {"success": False, "transaction_ref": None, "error": str(e)}
        except Exception as e:
            return {"success": False, "transaction_ref": None, "error": str(e)}
