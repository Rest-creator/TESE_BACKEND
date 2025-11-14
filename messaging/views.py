# messaging/views.py
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services.messaging_services import MessagingService
from .serializers.messaging_serializer import (
    ConversationListSerializer, 
    MessageSerializer, 
    CreateConversationSerializer,
    CreateMessageSerializer
)
from .models import Message

class ConversationListView(views.APIView):
    """
    GET: List all conversations for the current user.
    POST: Find or create a new 1-on-1 conversation.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        service = MessagingService()
        conversations = service.get_conversations_for_user(request.user)
        
        # We need to manually get the last message for each conversation
        # This is more efficient than a SerializerMethodField
        data = []
        for convo in conversations:
            last_msg = convo.messages.first() # .first() is correct due to ordering
            convo_data = ConversationListSerializer(convo).data
            convo_data['last_message'] = MessageSerializer(last_msg).data if last_msg else None
            data.append(convo_data)
            
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        This is the "find-or-create" endpoint.
        """
        serializer = CreateConversationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        service = MessagingService()
        
        try:
            conversation = service.find_or_create_conversation(
                current_user=request.user,
                seller_id=data['seller_id'],
                product_id=data.get('product_id')
            )
            # Serialize the newly found/created conversation
            serializer = ConversationListSerializer(conversation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class MessageListView(views.APIView):
    """
    GET: List all messages for a specific conversation.
    POST: Send a new message to that conversation.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, conversation_id):
        service = MessagingService()
        try:
            messages = service.get_messages_for_conversation(request.user, conversation_id)
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
            
    def post(self, request, conversation_id):
        serializer = CreateMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        service = MessagingService()
        try:
            message = service.send_message(
                user=request.user,
                conversation_id=conversation_id,
                text=serializer.validated_data['text']
            )
            serializer = MessageSerializer(message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({'error': "Message could not be sent."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)