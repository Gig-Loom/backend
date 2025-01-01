from django.urls import path
from . import views

urlpatterns = [
    path('chatrooms/', views.get_chat_list, name='get_chat_list'),
    path('chatrooms/create/', views.create_chat_room, name='create_chat_room'),
    path('chatrooms/<int:chatroom_id>/messages/', views.get_messages, name='get_messages'),
    path('chatrooms/<int:chatroom_id>/close/', views.close_chat_room, name='close_chatroom'),
    path('update-push-token/', views.update_push_token, name='update_push_token'),
    path('update-notification-settings/', views.update_notification_settings, name='update_notification_settings'),
]
