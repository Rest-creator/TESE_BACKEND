from rest_framework import serializers
from ..services.auth_service import AuthService

class SignupSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    location = serializers.CharField()

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        try:
            return AuthService.signup(validated_data)
        except ValueError as e:
            raise serializers.ValidationError(str(e))


class SigninSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        result = AuthService.signin(data["identifier"], data["password"])
        if not result:
            raise serializers.ValidationError("Invalid credentials")
        return result

class UserProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(source='username')
    email = serializers.EmailField(allow_null=True, allow_blank=True)
    phone = serializers.CharField(allow_null=True, allow_blank=True)
    location = serializers.CharField()
    business_name = serializers.CharField(allow_null=True, allow_blank=True)
    is_seller = serializers.SerializerMethodField()
    is_active = serializers.BooleanField()
    date_joined = serializers.DateTimeField()
    
    def get_is_seller(self, obj):
        # Example logic
        return getattr(obj, 'is_seller', False)

    @staticmethod
    def from_entity(entity):
        return UserProfileSerializer({
            "id": entity.id,
            "name": entity.name,
            "email": entity.email,
            "phone": entity.phone,
            "location": entity.location,
            "business_name": entity.business_name,
            "is_seller": entity.is_seller,
            "is_active": entity.is_active,
            "date_joined": entity.date_joined,
        })

