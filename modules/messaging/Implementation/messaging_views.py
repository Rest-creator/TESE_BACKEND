# interfaces/views/messaging_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..services.messaging_service import MessagingService
from ..repositories.messaging_repository import ConversationRepository, MessageRepository
from ..serializers.messaging_serializers import ConversationSerializer, MessageSerializer

class ConversationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    service = MessagingService(ConversationRepository(), MessageRepository())

    def create(self, request):
        product_id = request.data.get("product_id")
        recipient_id = request.data.get("recipient_id")
        convo = self.service.start_conversation(product_id, request.user.id, recipient_id)
        return Response(ConversationSerializer(convo).data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    service = MessagingService(ConversationRepository(), MessageRepository())

    def create(self, request):
        conversation_id = request.data.get("conversation_id")
        content = request.data.get("content")
        msg = self.service.send_message(conversation_id, request.user.id, content)
        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)

    def list(self, request, conversation_id=None):
        messages = self.service.get_conversation_messages(conversation_id)
        return Response(MessageSerializer(messages, many=True).data)
