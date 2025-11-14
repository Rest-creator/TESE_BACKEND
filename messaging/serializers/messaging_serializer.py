# messaging/serializers.py
from rest_framework import serializers
from ..models import Conversation, Message
from django.contrib.auth import get_user_model

# A simple serializer for user info inside other objects
class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'first_name', 'last_name'] # Add any other fields you need

class MessageSerializer(serializers.ModelSerializer):
    # We use SimpleUserSerializer to nest the sender's info
    sender = SimpleUserSerializer(read_only=True)
    
    # This field will be 'text' from the model
    text = serializers.CharField() 
    
    class Meta:
        model = Message
        # Match the frontend: 'conversation_id', not 'conversation'
        fields = ['id', 'conversation_id', 'sender', 'text', 'created_at']

class ConversationListSerializer(serializers.ModelSerializer):
    """
    Serializer for the list of conversations.
    Includes participants and the last message.
    """
    participants = SimpleUserSerializer(many=True, read_only=True)
    
    # 'last_message' will be populated from the service/view
    last_message = MessageSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'product', 'updated_at', 'last_message']

class CreateConversationSerializer(serializers.Serializer):
    """
    Serializer for validating the "find-or-create" request.
    """
    seller_id = serializers.IntegerField()
    product_id = serializers.IntegerField(required=False)

class CreateMessageSerializer(serializers.Serializer):
    """
    Serializer for validating a new message.
    """
    text = serializers.CharField(max_length=4000)