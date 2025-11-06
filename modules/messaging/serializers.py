from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Conversation, Message, MessageRead, MessageReaction, ConversationMember
from modules.auth.serializers.auth_serializers import UserProfileSerializer
from teseapi.models import Listing
import requests

class MessageSerializer(serializers.ModelSerializer):
    sender = UserProfileSerializer(read_only=True)
    reactions = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    shared_product_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'message_type', 'attachment_url', 
                 'attachment_type', 'attachment_name', 'shared_product', 'shared_product_data',
                 'is_read', 'is_edited', 'created_at', 'updated_at', 'reactions']
        read_only_fields = ['id', 'sender', 'created_at', 'updated_at', 'is_edited']
    
    def get_reactions(self, obj):
        reactions = {}
        for reaction in obj.reactions.all():
            reaction_type = reaction.reaction_type
            if reaction_type not in reactions:
                reactions[reaction_type] = []
            reactions[reaction_type].append({
                'user_id': reaction.user.id,
                'username': reaction.user.username
            })
        return reactions
    
    def get_is_read(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.read_receipts.filter(user=request.user).exists()
        return False
    
    def get_shared_product_data(self, obj):
        if obj.shared_product:
            return {
                'id': obj.shared_product.id,
                'name': obj.shared_product.name,
                'price': obj.shared_product.price,
                'image': obj.shared_product.product_images.first().image_url if obj.shared_product.product_images.exists() else None
            }
        return None

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserProfileSerializer(many=True, read_only=True)
    last_message = MessageSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'is_group', 'participants', 'last_message', 
                 'unread_count', 'other_participant', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.exclude(sender=request.user).filter(
                read_receipts__isnull=True
            ).count()
        return 0
    
    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and not obj.is_group:
            other_participants = obj.participants.exclude(id=request.user.id)
            if other_participants.exists():
                return UserProfileSerializer(other_participants.first()).data
        return None

class MessageCreateSerializer(serializers.ModelSerializer):
    attachment = serializers.FileField(write_only=True, required=False)
    receiver_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Message
        fields = ['content', 'message_type', 'shared_product', 'attachment', 'receiver_id']
    
    def validate(self, attrs):
        if not attrs.get('content') and not attrs.get('attachment') and not attrs.get('shared_product'):
            raise serializers.ValidationError("Message must have content, attachment, or shared product")
        return attrs
    
    def create(self, validated_data):
        request = self.context.get('request')
        conversation = self.context.get('conversation')
        attachment = validated_data.pop('attachment', None)
        receiver_id = validated_data.pop('receiver_id', None)
        
        # If no conversation provided, create or get one
        if not conversation and receiver_id:
            from teseapi.models import User as CustomUser
            try:
                receiver = CustomUser.objects.get(id=receiver_id)
                # Find existing conversation between these two users
                conversation = Conversation.objects.filter(
                    participants=request.user,
                    is_group=False
                ).filter(participants=receiver).first()
                
                if not conversation:
                    # Create new conversation
                    conversation = Conversation.objects.create(is_group=False)
                    conversation.participants.add(request.user, receiver)
                
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("Invalid receiver")
        
        if not conversation:
            raise serializers.ValidationError("Conversation is required")
        
        validated_data['sender'] = request.user
        validated_data['conversation'] = conversation
        
        # Handle file attachment
        if attachment:
            attachment_url = self.upload_attachment(attachment)
            if attachment_url:
                validated_data['attachment_url'] = attachment_url
                validated_data['attachment_name'] = attachment.name
                validated_data['attachment_type'] = self.get_file_type(attachment.name)
                if not validated_data.get('message_type'):
                    validated_data['message_type'] = 'image' if validated_data['attachment_type'].startswith('image') else 'file'
        
        # Set message type for product sharing
        if validated_data.get('shared_product'):
            validated_data['message_type'] = 'product_share'
        
        message = Message.objects.create(**validated_data)
        
        # Create notifications for other participants
        self.create_notifications(message)
        
        return message
    
    def upload_attachment(self, attachment):
        """Upload attachment to Bytescale"""
        try:
            from django.conf import settings
            
            api_key = getattr(settings, 'BYTESCALE_API_KEY', None)
            account_id = getattr(settings, 'BYTESCALE_ACCOUNT_ID', None)
            
            if not api_key or not account_id:
                return None
            
            url = f"https://api.bytescale.com/v2/accounts/{account_id}/uploads/binary"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
            }
            
            files = {
                'file': (attachment.name, attachment, attachment.content_type)
            }
            
            response = requests.post(url, headers=headers, files=files)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('fileUrl')
            
        except Exception as e:
            print(f"Error uploading attachment: {e}")
        
        return None
    
    def get_file_type(self, filename):
        """Get file type from filename"""
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
        video_extensions = ['mp4', 'avi', 'mov', 'wmv', 'flv']
        audio_extensions = ['mp3', 'wav', 'ogg', 'aac']
        
        if extension in image_extensions:
            return f'image/{extension}'
        elif extension in video_extensions:
            return f'video/{extension}'
        elif extension in audio_extensions:
            return f'audio/{extension}'
        else:
            return f'application/{extension}'
    
    def is_valid(self, raise_exception=False):
        valid = super().is_valid(raise_exception=raise_exception)
        if not valid:
            print("MessageCreateSerializer errors:", self.errors)
        return valid

    
    def create_notifications(self, message):
        """Create notifications for message recipients"""
        from .models import MessageNotification
        
        # Notify all participants except sender
        participants = message.conversation.participants.exclude(id=message.sender.id)
        
        for participant in participants:
            MessageNotification.objects.get_or_create(
                recipient=participant,
                message=message
            )

class ConversationCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    product_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Conversation
        fields = ['title', 'is_group', 'participant_ids', 'product_id']
    
    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids')
        product_id = validated_data.pop('product_id', None)
        request = self.context.get('request')
        
        # Create conversation
        conversation = Conversation.objects.create(**validated_data)
        
        # Add current user as participant
        conversation.participants.add(request.user)
        
        # Add other participants
        from teseapi.models import User as CustomUser
        for participant_id in participant_ids:
            try:
                user = CustomUser.objects.get(id=participant_id)
                conversation.participants.add(user)
            except CustomUser.DoesNotExist:
                continue
        
        # Link to product if provided
        if product_id:
            try:
                product = Listing.objects.get(id=product_id)
                conversation.content_type = ContentType.objects.get_for_model(Listing)
                conversation.object_id = product.id
                conversation.save()
            except Listing.DoesNotExist:
                pass
        
        return conversation

class MessageReactionSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ['id', 'user', 'reaction_type', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
