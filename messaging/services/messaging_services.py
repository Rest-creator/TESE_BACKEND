# messaging/services.py
from ..repositories.messaging_repository import ConversationRepository, MessageRepository
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from ..models import Conversation, Message

User = get_user_model()

class MessagingService:
    def __init__(self):
        self.convo_repo = ConversationRepository()
        self.message_repo = MessageRepository()

    def get_conversations_for_user(self, user: User):
        """
        Get all conversation for the logged-in user.
        """
        return self.convo_repo.list_for_user(user)

    def get_messages_for_conversation(self, user: User, conversation_id: int):
        """
        Get all messages for a conversation,
        but *only* if the user is a participant.
        """
        conversation = self.convo_repo.get_by_id(conversation_id)
        if not conversation or user not in conversation.participants.all():
            raise PermissionDenied("You do not have access to this conversation.")
        
        return self.message_repo.list_by_conversation(conversation_id)

    def find_or_create_conversation(self, current_user: User, seller_id: int, product_id: int = None) -> Conversation:
        """
        This is the core "find-or-create" logic.
        """
        try:
            seller = User.objects.get(id=seller_id)
        except User.DoesNotExist:
            raise ValueError("Seller not found.")

        if current_user.id == seller_id:
            raise ValueError("You cannot start a conversation with yourself.")

        # 1. Try to find an existing 1-on-1 conversation
        conversation = self.convo_repo.find_1on1_conversation(current_user, seller)
        
        # 2. If not found, create it
        if not conversation:
            conversation = self.convo_repo.create_1on1_conversation(current_user, seller, product_id)
            
        return conversation

    def send_message(self, user: User, conversation_id: int, text: str) -> Message:
        """
        Sends a new message to a conversation,
        but *only* if the user is a participant.
        """
        conversation = self.convo_repo.get_by_id(conversation_id)
        if not conversation or user not in conversation.participants.all():
            raise PermissionDenied("You do not have access to this conversation.")

        return self.message_repo.create_message(conversation, user, text)