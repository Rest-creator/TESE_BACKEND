# core/entities/messaging.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ConversationEntity:
    id: Optional[int]
    product_id: int
    initiator_id: int
    recipient_id: int
    created_at: datetime

@dataclass
class MessageEntity:
    id: Optional[int]
    conversation_id: int
    sender_id: int
    content: str
    created_at: datetime
