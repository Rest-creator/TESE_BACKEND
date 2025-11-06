from teseapi.models import User

class UserRepository:
    @staticmethod
    def create_user(validated_data):
        name = validated_data.get("name")
        first, *rest = name.split(" ", 1)
        last = rest[0] if rest else ""

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            phone_number=validated_data.get("phone"),
            first_name=first,
            last_name=last,
            password=validated_data["password"],
            location=validated_data.get("location"),
        )
        return user

    @staticmethod
    def find_by_email(email):
        return User.objects.filter(email__iexact=email).first()

    @staticmethod
    def find_by_phone(phone):
        return User.objects.filter(phone_number=phone).first()
