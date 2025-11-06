import re
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from ..repositories.user_repository import UserRepository
from ..entities.user_entity import UserEntity

class AuthService:
    @staticmethod
    def signup(data):
        email = data.get("email")
        phone = data.get("phone")

        # ✅ username logic
        if email:
            data["username"] = email
        elif phone:
            data["username"] = phone
        else:
            raise ValueError("Either email or phone is required")

        # ✅ check duplicates
        if email and UserRepository.find_by_email(email):
            raise ValueError("Email already exists")
        if phone and UserRepository.find_by_phone(phone):
            raise ValueError("Phone already exists")

        # ✅ create user
        user = UserRepository.create_user(data)
        refresh = RefreshToken.for_user(user)

        return {
            "user": UserEntity.from_model(user),
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @staticmethod
    def signin(identifier, password):
        user = None
        if re.fullmatch(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", identifier):
            user = UserRepository.find_by_email(identifier)
        elif re.fullmatch(r"^\+[1-9]\d{6,14}$", identifier):
            user = UserRepository.find_by_phone(identifier)

        if user and not user.check_password(password):
            user = None

        if not user:
            user = authenticate(username=identifier, password=password)

        if not user:
            return None

        refresh = RefreshToken.for_user(user)
        return {
            "user": UserEntity.from_model(user),
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
