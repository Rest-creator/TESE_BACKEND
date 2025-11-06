# In your messaging/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('conversations/', views.conversations, name='conversations'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    # Handle GET (list messages) and POST (send message) for a conversation
    path('conversations/<int:conversation_id>/messages/', views.conversation_messages, name='conversation_messages'),
    path('conversations/<int:conversation_id>/read/', views.mark_messages_read, name='mark_messages_read'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/<int:message_id>/react/', views.react_to_message, name='react_to_message'),
    path('notifications/', views.message_notifications, name='message_notifications'),
    path('start-conversation/', views.start_conversation, name='start_conversation'),
]