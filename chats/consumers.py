import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)
import requests
from requests.exceptions import ConnectionError, HTTPError

User = get_user_model()

active_users = {}

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        session = requests.Session()
        session.headers.update({
            "accept": "application/json",
            "accept-encoding": "gzip, deflate",
            "content-type": "application/json",
        })
        self.push_client = PushClient(session=session)

    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return
            
        self.chat_room_id = self.scope['url_route']['kwargs']['chat_room_id']
        self.room_group_name = f"chat_{self.chat_room_id}"
        self.user_id = str(self.scope["user"].id)

        active_users[self.user_id] = self.chat_room_id

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if self.user_id in active_users:
            del active_users[self.user_id]

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def save_message(self, chat_room_id, sender_id, message):
        try:
            chat_room = ChatRoom.objects.select_for_update().get(id=chat_room_id)
            return Message.objects.create(
                room=chat_room,
                sender_id=sender_id,
                content=message
            )
        except ChatRoom.DoesNotExist:
            raise ValueError("Chat room does not exist")

    @database_sync_to_async
    def get_recipient_info(self, chat_room_id, sender_id):
        chat_room = ChatRoom.objects.select_related('buyer', 'seller').get(id=chat_room_id)
        is_sender_seller = str(chat_room.seller.id) == str(sender_id)
        recipient = chat_room.buyer if is_sender_seller else chat_room.seller
        recipient_id = str(recipient.id)
        
        try:
            push_token = recipient.userprofile.push_token
            return {
                'recipient_id': recipient_id,
                'push_token': push_token
            }
        except:
            return {
                'recipient_id': recipient_id,
                'push_token': None
            }

    @database_sync_to_async
    def deactivate_push_token(self, token):
        from accounts.models import UserProfile
        UserProfile.objects.filter(push_token=token).update(push_token=None)

    async def send_push_notification(self, token, message, sender_name):
        try:
            push_message = PushMessage(
                to=token,
                body=f"{sender_name}: {message}",
                data={
                    'type': 'chat_message',
                    'chat_room_id': self.chat_room_id
                },
                sound="default",
                title="New Message"
            )

            response = await sync_to_async(self.push_client.publish)(push_message)
            await sync_to_async(response.validate_response)()

        except PushServerError as exc:
            print(f"Push Server Error: {exc.errors}")
            print(f"Response data: {exc.response_data}")
        except (ConnectionError, HTTPError) as exc:
            print(f"Connection Error: {exc}")
        except DeviceNotRegisteredError:
            await self.deactivate_push_token(token)
        except PushTicketError as exc:
            print(f"Push Ticket Error: {exc.push_response._asdict()}")
        except Exception as e:
            print(f"Unknown error sending push notification: {str(e)}")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_id = self.scope["user"].id

        saved_message = await self.save_message(self.chat_room_id, sender_id, message)

        recipient_info = await self.get_recipient_info(self.chat_room_id, sender_id)
        recipient_id = recipient_info['recipient_id']
        
        if recipient_id not in active_users or active_users[recipient_id] != self.chat_room_id:
            push_token = recipient_info['push_token']
            if push_token:
                sender_name = self.scope["user"].get_full_name() or "New message"
                await self.send_push_notification(push_token, message, sender_name)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id,
        }))
        
