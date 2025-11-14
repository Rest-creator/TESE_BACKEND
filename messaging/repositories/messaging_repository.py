# messaging/repositories.py
from django.db.models import Q
from ..models import Conversation, Message, models
from django.conf import settings
from teseapi.models import Listing # Adjust this import

User = settings.AUTH_USER_MODEL

class ConversationRepository:
    def get_by_id(self, conversation_id: int) -> Conversation | None:
        try:
            return Conversation.objects.prefetch_related('participants').get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None

    def list_for_user(self, user: User) -> models.QuerySet[Conversation]:
        """
        Returns all conversations a user is a participant in,
        ordered by the most recently updated.
        """
        return user.conversations.all().prefetch_related('participants')

    def find_1on1_conversation(self, user1: User, user2: User) -> Conversation | None:
        """
        Finds an existing 1-on-1 conversation between two users.
        """
        try:
            # Find a conversation that has *only* these two participants
            return Conversation.objects.annotate(
                num_participants=models.Count('participants')
            ).filter(
                num_participants=2,
                participants=user1
            ).filter(
                participants=user2
            ).first()
        except Conversation.DoesNotExist:
            return None

    def create_1on1_conversation(self, user1: User, user2: User, product_id: int = None) -> Conversation:
        """
        Creates a new 1-on-1 conversation.
        """
        product = None
        if product_id:
            try:
                product = Listing.objects.get(id=product_id)
            except Listing.DoesNotExist:
                pass # Product not found, continue without it

        conversation = Conversation.objects.create(product=product)
        conversation.participants.add(user1, user2)
        return conversation

class MessageRepository:
    def list_by_conversation(self, conversation_id: int) -> models.QuerySet[Message]:
        """
        Returns all messages for a given conversation.
        """
        return Message.objects.filter(conversation_id=conversation_id).select_related('sender')

    def create_message(self, conversation: Conversation, sender: User, text: str) -> Message:
        """
        Creates a new message and updates the conversation's 'updated_at' timestamp.
        """
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            text=text
        )
        
        # This is key: "bump" the conversation to the top of the list
        conversation.updated_at = message.created_at
        conversation.save(update_fields=['updated_at'])
        
        return message