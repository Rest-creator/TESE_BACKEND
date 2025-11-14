# messaging/urls.py
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # path('api/messaging/conversations/')
    path(
        'conversations/', 
        views.ConversationListView.as_view(), 
        name='conversation-list'
    ),
    
    # path('api/messaging/conversations/<int:conversation_id>/messages/')
    path(
        'conversations/<int:conversation_id>/messages/', 
        views.MessageListView.as_view(), 
        name='message-list'
    ),
]