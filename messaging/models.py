# In your messages app's models.py

from django.db import models
from django.conf import settings
from teseapi.models import Listing

class Conversation(models.Model):
    """
    A simple conversation between two or more users.
    For your 1-on-1 use case, it will just have two participants.
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    
    # Optional: Link to the product this chat started from.
    # Assumes your listing model is 'teseapi.Listing'
    # This makes the "find-or-create" logic much easier.
    product = models.ForeignKey(
        Listing,
        on_delete=models.SET_NULL, # Don't delete chat if product is deleted
        null=True,
        blank=True,
        related_name='conversations'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Used to sort conversations

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        # A simple name for the admin panel
        participant_names = ", ".join(
            [user.username for user in self.participants.all()]
        )
        return f"Conversation ({self.id}) between: {participant_names}"

class Message(models.Model):
    """
    A single message in a conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    
    # Renamed from 'content' to 'text' to match your frontend context
    text = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Order messages from oldest to newest
        ordering = ['created_at'] 

    def __str__(self):
        return f"Message from {self.sender.username} in convo {self.conversation.id}"