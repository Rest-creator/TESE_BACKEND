class UserEntity:
    def __init__(self, id, username, email, phone_number, first_name, last_name, location, role=None, status=None):
        self.id = id
        self.username = username
        self.email = email
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.location = location
        self.role = role
        self.status = status

    @staticmethod
    def from_model(user_model):
        return UserEntity(
            id=user_model.id,
            username=user_model.username,
            email=user_model.email,
            phone_number=user_model.phone_number,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            location=user_model.location,
            role=getattr(user_model, "role", None),
            status=getattr(user_model, "status", None),
        )
