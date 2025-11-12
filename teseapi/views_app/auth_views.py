from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from modules.auth.serializers.auth_serializers import SignupSerializer, SigninSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@method_decorator(csrf_exempt, name='dispatch')
class SignupView(APIView):
    permission_classes = [AllowAny]  # No auth required
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                "message": "Account created successfully",
                "user": vars(result["user"]),
                "access": result["access"],
                "refresh": result["refresh"]
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class SigninView(APIView):
    permission_classes = [AllowAny]  # No auth required
    def post(self, request):
        serializer = SigninSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.validated_data
            return Response({
                "message": "Login successful",
                "user": vars(result["user"]),
                "access": result["access"],
                "refresh": result["refresh"]
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
