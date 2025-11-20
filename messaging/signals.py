# messaging/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Message

@receiver(post_save, sender=Message)
def send_message_to_socket(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        room_group_name = f'chat_{instance.conversation.id}'
        
        # Prepare the data exactly as the frontend expects it
        message_data = {
            'id': instance.id,
            'text': instance.text,
            'sender': {
                'id': instance.sender.id,
                'username': instance.sender.username,
                'first_name': instance.sender.first_name,
                # Add other user fields if needed
            },
            'conversation': instance.conversation.id,
            'created_at': instance.created_at.isoformat(),
            'is_read': instance.is_read
        }

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )