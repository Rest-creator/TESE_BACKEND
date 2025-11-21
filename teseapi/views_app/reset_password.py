from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
import logging

# Get the active user model
User = get_user_model()
logger = logging.getLogger(__name__)

def send_sms_mock(phone_number, message):
    """
    REAL WORLD: This is where you would call Twilio/ClickSend API.
    DEV MODE: We print to console so you can copy the link.
    """
    print(f"\n========== [MOCK SMS GATEWAY] ==========")
    print(f"To: {phone_number}")
    print(f"Message: {message}")
    print(f"========================================\n")
    return True

class RequestPasswordResetView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # 1. Accept 'identifier' (could be email or phone)
        identifier = request.data.get('identifier') or request.data.get('email')
        
        if not identifier:
            return Response({"error": "Email or Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        is_email = False

        # 2. Detect if it's an email or phone
        if '@' in identifier:
            is_email = True
            user = User.objects.filter(email=identifier).first()
        else:
            # Assuming it's a phone number
            # Note: Your User model calls this field 'phone_number'
            user = User.objects.filter(phone_number=identifier).first()

        if user:
            # 3. Generate Token (Works the same for Email or Phone)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # 4. Construct the Link
            reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}&uid={uid}"
            
            # 5. Send based on type
            if is_email:
                # Send Email
                try:
                    send_mail(
                        subject="Reset your Tese Marketplace Password",
                        message=f"Click the link to reset your password: {reset_link}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    logger.error(f"Email failed: {e}")
                    # In production, maybe don't tell the user it failed for security
            else:
                # Send SMS
                # Since SMS has character limits, keep it short
                sms_message = f"Tese Marketplace: Reset your password here: {reset_link}"
                send_sms_mock(user.phone_number, sms_message)

        # Security: Always return 200 to prevent user enumeration
        return Response(
            {"message": "If an account exists, a reset link has been sent."}, 
            status=status.HTTP_200_OK
        )

# The Confirm View stays exactly the same!
class ResetPasswordConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            uidb64 = request.data.get('uid')
            token = request.data.get('token')
            password = request.data.get('password')

            if not uidb64 or not token or not password:
                 return Response({"error": "Missing data"}, status=status.HTTP_400_BAD_REQUEST)

            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            if not default_token_generator.check_token(user, token):
                return Response(
                    {"error": "Token is invalid or expired"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(password)
            user.save()

            return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
             return Response(
                {"error": "Invalid request"}, 
                status=status.HTTP_400_BAD_REQUEST
            )