from django.conf import settings
from paynow import Paynow
from typing import Optional, Dict

class PaynowGateway:
    def __init__(self):
        # instantiate Paynow with integration id/key and result/return URLs
        self.paynow = Paynow(
            settings.PAYNOW_INTEGRATION_ID,
            settings.PAYNOW_SECRET_KEY,
            settings.PAYNOW_RESULT_URL,
            settings.PAYNOW_RETURN_URL,
        )

    def create_payment_redirect(self, reference: str, email: str, amount: float) -> Dict:
        """
        Create a Paynow payment and return redirect info.
        - reference: your internal reference (invoice id, order id)
        - email: customer email (required by SDK)
        - amount: decimal amount in currency unit (e.g., 10.50)
        Returns dict with keys: success (bool), redirect_url, poll_url, message
        """
        try:
            payment = self.paynow.create_payment(reference, email)
            # SDK expects prices as floats; add items (you can also store line items separately)
            payment.add('Payment', amount)

            # Use send() for web checkout (returns redirect_url & poll_url)
            response = self.paynow.send(payment)

            if response.success:
                return {
                    "success": True,
                    "redirect_url": response.redirect_url,
                    "poll_url": response.poll_url,
                    "message": "Redirect user to redirect_url and save poll_url for polling."
                }
            else:
                return {"success": False, "message": f"Paynow send failed: {response.error}"}

        except Exception as e:
            return {"success": False, "message": str(e)}

    def send_mobile_payment(self, reference: str, email: str, amount: float, phone: str, mobile_method: str='ecocash') -> Dict:
        """
        Trigger express mobile payment (Ecocash/Onemoney) which returns poll_url and instructions.
        mobile_method: 'ecocash' or 'onemoney' (per Paynow docs)
        """
        try:
            payment = self.paynow.create_payment(reference, email)
            payment.add('Payment', amount)
            response = self.paynow.send_mobile(payment, phone, mobile_method)
            if response.success:
                return {"success": True, "poll_url": response.poll_url, "instructions": response.instructions}
            else:
                return {"success": False, "message": getattr(response, "error", "send_mobile failed")}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def check_status(self, poll_url: str) -> Dict:
        """
        Poll transaction status via the poll_url returned by Paynow earlier.
        Returns a dict with 'paid' boolean and raw status
        """
        try:
            status = self.paynow.check_transaction_status(poll_url)
            return {"paid": getattr(status, "paid", False), "status": getattr(status, "status", None)}
        except Exception as e:
            return {"paid": False, "error": str(e)}
