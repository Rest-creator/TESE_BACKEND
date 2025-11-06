from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Max
from django.utils import timezone
from .models import Conversation, Message, MessageRead, MessageReaction, MessageNotification
from .serializers import (
    ConversationSerializer, MessageSerializer, 
    MessageCreateSerializer, ConversationCreateSerializer,
    MessageReactionSerializer
)

class MessagePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def conversations(request):
    """Get user's conversations or create a new conversation"""
    if request.method == 'GET':
        try:
            # Get conversations where user is a participant
            user_conversations = Conversation.objects.filter(
                participants=request.user
            ).prefetch_related('participants', 'messages').annotate(
                last_message_time=Max('messages__created_at')
            ).order_by('-last_message_time')
            
            serializer = ConversationSerializer(user_conversations, many=True, context={'request': request})
            return Response({
                'success': True,
                'conversations': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            print(request.data)
            serializer = ConversationCreateSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                conversation = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Conversation created successfully',
                    'conversation': ConversationSerializer(conversation, context={'request': request}).data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Conversation creation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def conversation_messages(request, conversation_id):
    """
    Handle messages in a conversation:
    - GET: Get all messages in the conversation
    - POST: Send a new message in the conversation
    """
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
        
        if request.method == 'GET':
            messages = Message.objects.filter(conversation=conversation).order_by('created_at')
            return Response({
                'success': True,
                'messages': [{
                    'id': msg.id,
                    'content': msg.content,
                    'sender_id': msg.sender.id,
                    'created_at': msg.created_at.isoformat(),
                    # Add other message fields as needed
                } for msg in messages]
            })
            
        elif request.method == 'POST':
            serializer = MessageCreateSerializer(
                data=request.data, 
                context={
                    'request': request,
                    'conversation': conversation
                }
            )
            
            if serializer.is_valid():
                message = serializer.save()
                return Response({
                    'success': True,
                    'message': MessageSerializer(message).data
                }, status=status.HTTP_201_CREATED)
                
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Conversation.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Conversation not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    """Get conversation details and messages"""
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
        
        # Get messages
        messages = conversation.messages.filter(
            is_deleted=False
        ).select_related('sender').prefetch_related('reactions', 'read_receipts').order_by('-created_at')
        
        # Paginate messages
        paginator = MessagePagination()
        page = paginator.paginate_queryset(messages, request)
        
        if page is not None:
            message_serializer = MessageSerializer(page, many=True, context={'request': request})
            conversation_data = ConversationSerializer(conversation, context={'request': request}).data
            
            return paginator.get_paginated_response({
                'success': True,
                'conversation': conversation_data,
                'messages': message_serializer.data
            })
        
        message_serializer = MessageSerializer(messages, many=True, context={'request': request})
        conversation_data = ConversationSerializer(conversation, context={'request': request}).data
        
        return Response({
            'success': True,
            'conversation': conversation_data,
            'messages': message_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Conversation.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Conversation not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, conversation_id=None):
    """Send a message in a conversation"""
    try:
        print("REQUEST DATA:", request.data)
        conversation = None
        if conversation_id:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=request.user
            )
            print("Found conversation:", conversation.id)
        
        serializer = MessageCreateSerializer(
            data=request.data, 
            context={'request': request, 'conversation': conversation}
        )
        
        print("Message serializer is valid?", serializer.is_valid())
        if not serializer.is_valid():
            print("Message serializer errors:", serializer.errors)
        
        if serializer.is_valid():
            message = serializer.save()
            print("Message sent successfully:", message.id)
            return Response({
                'success': True,
                'message': 'Message sent successfully',
                'data': MessageSerializer(message, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Message sending failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Conversation.DoesNotExist:
        print("Conversation not found:", conversation_id)
        return Response({
            'success': False,
            'message': 'Conversation not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print("Exception in send_message:", str(e))
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def message_detail(request, message_id):
    """Update or delete a message"""
    try:
        message = Message.objects.get(
            id=message_id,
            sender=request.user,
            is_deleted=False
        )
        
        if request.method == 'PUT':
            # Only allow editing text messages
            if message.message_type != 'text':
                return Response({
                    'success': False,
                    'message': 'Only text messages can be edited'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            content = request.data.get('content')
            if not content:
                return Response({
                    'success': False,
                    'message': 'Content is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            message.content = content
            message.is_edited = True
            message.edited_at = timezone.now()
            message.save()
            
            return Response({
                'success': True,
                'message': 'Message updated successfully',
                'data': MessageSerializer(message, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'DELETE':
            message.is_deleted = True
            message.save()
            
            return Response({
                'success': True,
                'message': 'Message deleted successfully'
            }, status=status.HTTP_200_OK)
    
    except Message.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Message not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_read(request, conversation_id):
    """Mark messages as read in a conversation"""
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
        
        # Get unread messages from other participants
        unread_messages = conversation.messages.exclude(
            sender=request.user
        ).exclude(
            read_receipts__user=request.user
        ).filter(is_deleted=False)
        
        # Create read receipts
        read_receipts = []
        for message in unread_messages:
            read_receipts.append(MessageRead(
                message=message,
                user=request.user
            ))
        
        MessageRead.objects.bulk_create(read_receipts, ignore_conflicts=True)
        
        return Response({
            'success': True,
            'message': f'Marked {len(read_receipts)} messages as read'
        }, status=status.HTTP_200_OK)
        
    except Conversation.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Conversation not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def react_to_message(request, message_id):
    """Add or remove reaction to a message"""
    try:
        message = Message.objects.get(id=message_id, is_deleted=False)
        
        # Check if user is participant in the conversation
        if not message.conversation.participants.filter(id=request.user.id).exists():
            return Response({
                'success': False,
                'message': 'You are not a participant in this conversation'
            }, status=status.HTTP_403_FORBIDDEN)
        
        reaction_type = request.data.get('reaction_type')
        if not reaction_type:
            return Response({
                'success': False,
                'message': 'Reaction type is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already reacted
        existing_reaction = MessageReaction.objects.filter(
            message=message,
            user=request.user
        ).first()
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # Remove reaction
                existing_reaction.delete()
                return Response({
                    'success': True,
                    'message': 'Reaction removed',
                    'reacted': False
                }, status=status.HTTP_200_OK)
            else:
                # Update reaction
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                return Response({
                    'success': True,
                    'message': 'Reaction updated',
                    'reacted': True,
                    'reaction_type': reaction_type
                }, status=status.HTTP_200_OK)
        else:
            # Add new reaction
            MessageReaction.objects.create(
                message=message,
                user=request.user,
                reaction_type=reaction_type
            )
            return Response({
                'success': True,
                'message': 'Reaction added',
                'reacted': True,
                'reaction_type': reaction_type
            }, status=status.HTTP_201_CREATED)
        
    except Message.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Message not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_notifications(request):
    """Get message notifications for current user"""
    try:
        notifications = MessageNotification.objects.filter(
            recipient=request.user
        ).select_related('message__sender', 'message__conversation').order_by('-created_at')
        
        # Mark as read if requested
        mark_read = request.GET.get('mark_read') == 'true'
        if mark_read:
            notifications.update(is_read=True)
        
        notification_data = []
        for notification in notifications[:50]:  # Limit to 50 recent notifications
            notification_data.append({
                'id': notification.id,
                'sender': {
                    'id': notification.message.sender.id,
                    'username': notification.message.sender.username,
                    'full_name': notification.message.sender.get_full_name() or notification.message.sender.username
                },
                'message': {
                    'id': notification.message.id,
                    'content': notification.message.content[:100] + '...' if len(notification.message.content) > 100 else notification.message.content,
                    'message_type': notification.message.message_type
                },
                'conversation': {
                    'id': notification.message.conversation.id,
                    'title': notification.message.conversation.title or f"Chat with {notification.message.sender.username}"
                },
                'is_read': notification.is_read,
                'created_at': notification.created_at
            })
        
        return Response({
            'success': True,
            'notifications': notification_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_conversation(request):
    """Start a new conversation with a user (shortcut endpoint)"""
    try:
        print("REQUEST DATA:", request.data)
        receiver_id = request.data.get('receiver_id')
        initial_message = request.data.get('message', '')
        product_id = request.data.get('product_id')
        
        if not receiver_id:
            print("Missing receiver_id")
            return Response({
                'success': False,
                'message': 'Receiver ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from teseapi.models import User as CustomUser
        try:
            receiver = CustomUser.objects.get(id=receiver_id)
            print("Found receiver:", receiver.id, receiver.username)
        except CustomUser.DoesNotExist:
            print("Receiver does not exist")
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check for existing conversation
        existing_conversation = Conversation.objects.filter(
            participants=request.user,
            is_group=False
        ).filter(participants=receiver).first()
        
        if existing_conversation:
            conversation = existing_conversation
            print("Using existing conversation:", conversation.id)
        else:
            conversation = Conversation.objects.create(is_group=False)
            conversation.participants.add(request.user, receiver)
            print("Created new conversation:", conversation.id)
            
            if product_id:
                try:
                    from teseapi.models import Listing
                    from django.contrib.contenttypes.models import ContentType
                    product = Listing.objects.get(id=product_id)
                    conversation.content_type = ContentType.objects.get_for_model(Listing)
                    conversation.object_id = product.id
                    conversation.save()
                    print("Linked conversation to product:", product.id)
                except Listing.DoesNotExist:
                    print("Product does not exist:", product_id)
        
        # Send initial message
        if initial_message:
            message_data = {
                'content': initial_message,
                'message_type': 'text'
            }
            print("Initial message data:", message_data)
            
            message_serializer = MessageCreateSerializer(
                data=message_data,
                context={'request': request, 'conversation': conversation}
            )
            
            if message_serializer.is_valid():
                message_serializer.save()
                print("Initial message sent successfully")
            else:
                print("Message serializer errors:", message_serializer.errors)
        
        conversation_data = ConversationSerializer(conversation, context={'request': request}).data
        print("Returning conversation data:", conversation_data)
        
        return Response({
            'success': True,
            'message': 'Conversation started successfully',
            'conversation': conversation_data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print("Exception in start_conversation:", str(e))
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
