# infrastructure/repositories/messaging_repository.py
from typing import List
from ..entities.messaging import ConversationEntity, MessageEntity
from ..Implementation.messaging_models import Conversation, Message  # Django ORM models

class ConversationRepository:
    def create(self, product_id: int, initiator_id: int, recipient_id: int) -> ConversationEntity:
        convo = Conversation.objects.create(
            product_id=product_id,
            initiator_id=initiator_id,
            recipient_id=recipient_id
        )
        return ConversationEntity(
            id=convo.id,
            product_id=convo.product_id,
            initiator_id=convo.initiator_id,
            recipient_id=convo.recipient_id,
            created_at=convo.created_at
        )

    def get_by_id(self, convo_id: int) -> ConversationEntity:
        convo = Conversation.objects.get(id=convo_id)
        return ConversationEntity(
            id=convo.id,
            product_id=convo.product_id,
            initiator_id=convo.initiator_id,
            recipient_id=convo.recipient_id,
            created_at=convo.created_at
        )


class MessageRepository:
    def create(self, conversation_id: int, sender_id: int, content: str) -> MessageEntity:
        msg = Message.objects.create(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content
        )
        return MessageEntity(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_id=msg.sender_id,
            content=msg.content,
            created_at=msg.created_at
        )

    def get_messages(self, conversation_id: int) -> List[MessageEntity]:
        msgs = Message.objects.filter(conversation_id=conversation_id).order_by("created_at")
        return [
            MessageEntity(
                id=m.id,
                conversation_id=m.conversation_id,
                sender_id=m.sender_id,
                content=m.content,
                created_at=m.created_at
            )
            for m in msgs
        ]
