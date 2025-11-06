# core/services/messaging_service.py
from ..entities.messaging import ConversationEntity, MessageEntity
from ..repositories.messaging_repository import (
    ConversationRepository, MessageRepository
)

class MessagingService:
    def __init__(self, conversation_repo: ConversationRepository, message_repo: MessageRepository):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo

    def start_conversation(self, product_id: int, initiator_id: int, recipient_id: int) -> ConversationEntity:
        return self.conversation_repo.create(product_id, initiator_id, recipient_id)

    def send_message(self, conversation_id: int, sender_id: int, content: str) -> MessageEntity:
        return self.message_repo.create(conversation_id, sender_id, content)

    def get_conversation_messages(self, conversation_id: int):
        return self.message_repo.get_messages(conversation_id)
