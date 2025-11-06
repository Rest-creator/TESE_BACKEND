# interfaces/serializers/messaging_serializers.py
from rest_framework import serializers
from ..entities.messaging import ConversationEntity, MessageEntity

class ConversationSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    product_id = serializers.IntegerField()
    initiator_id = serializers.IntegerField()
    recipient_id = serializers.IntegerField()
    created_at = serializers.DateTimeField()

    def to_representation(self, instance: ConversationEntity):
        return {
            "id": instance.id,
            "product_id": instance.product_id,
            "initiator_id": instance.initiator_id,
            "recipient_id": instance.recipient_id,
            "created_at": instance.created_at,
        }


class MessageSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    conversation_id = serializers.IntegerField()
    sender_id = serializers.IntegerField()
    content = serializers.CharField()
    created_at = serializers.DateTimeField()

    def to_representation(self, instance: MessageEntity):
        return {
            "id": instance.id,
            "conversation_id": instance.conversation_id,
            "sender_id": instance.sender_id,
            "content": instance.content,
            "created_at": instance.created_at,
        }
