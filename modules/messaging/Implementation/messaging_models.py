# marketplace/models.py
from django.db import models
from django.conf import settings

class Conversation(models.Model):
    product = models.ForeignKey("swapapp.Product", on_delete=models.CASCADE, related_name="conversations")
    initiator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="initiated_conversations")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Ensures that a conversation between two users for a specific product is unique
        unique_together = ('product', 'initiator', 'recipient')

    def __str__(self):
        return f"Conversation for {self.product.name} between {self.initiator.username} and {self.recipient.username}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} in conversation {self.conversation.id}"

