import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Message, Conversation, UserProfile

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.user_profile = await self.get_user_profile()
        self.room_group_name = f"user_{self.user_profile.id}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'read_messages':
            await self.handle_read_messages(text_data_json)
        elif message_type == 'typing':
            await self.handle_typing(text_data_json)

    async def handle_chat_message(self, data):
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        message_type = data.get('message_type', 'text')
        
        # Save message to database
        message = await self.save_message(receiver_id, content, message_type)
        
        # Get receiver's room group name
        receiver_group = f"user_{receiver_id}"
        
        # Send message to receiver
        await self.channel_layer.group_send(
            receiver_group,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'sender_id': self.user_profile.id,
                    'sender_name': self.user.username,
                    'content': message.content,
                    'message_type': message.message_type,
                    'created_at': message.created_at.isoformat(),
                }
            }
        )
        
        # Send confirmation to sender
        await self.send(text_data=json.dumps({
            'type': 'message_sent',
            'message_id': message.id
        }))

    async def handle_read_messages(self, data):
        message_ids = data.get('message_ids', [])
        conversation_id = data.get('conversation_id')
        
        # Mark messages as read
        await self.mark_messages_as_read(message_ids)
        
        # Notify sender that messages were read
        if conversation_id:
            conversation = await self.get_conversation(conversation_id)
            other_participant = await self.get_other_participant(conversation)
            
            await self.channel_layer.group_send(
                f"user_{other_participant.id}",
                {
                    'type': 'messages_read',
                    'message_ids': message_ids
                }
            )

    async def handle_typing(self, data):
        receiver_id = data.get('receiver_id')
        is_typing = data.get('is_typing')
        
        await self.channel_layer.group_send(
            f"user_{receiver_id}",
            {
                'type': 'typing',
                'user_id': self.user_profile.id,
                'is_typing': is_typing
            }
        )

    async def chat_message(self, event):
        """Handle incoming chat message"""
        await self.send(text_data=json.dumps(event))

    async def messages_read(self, event):
        """Handle message read notification"""
        await self.send(text_data=json.dumps(event))

    async def typing(self, event):
        """Handle typing notification"""
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_user_profile(self):
        return UserProfile.objects.get(user=self.user)

    @database_sync_to_async
    def save_message(self, receiver_id, content, message_type):
        receiver = UserProfile.objects.get(id=receiver_id)
        conversation = Conversation.objects.filter(
            participants=self.user_profile
        ).filter(
            participants=receiver
        ).first()
        
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(self.user_profile, receiver)
        
        message = Message.objects.create(
            sender=self.user_profile,
            receiver=receiver,
            content=content,
            message_type=message_type,
            subject="New message"  # You might want to make this more dynamic
        )
        
        conversation.last_message = message
        conversation.save()
        
        return message

    @database_sync_to_async
    def mark_messages_as_read(self, message_ids):
        messages = Message.objects.filter(
            id__in=message_ids,
            receiver=self.user_profile,
            is_read=False
        )
        for message in messages:
            message.mark_as_read()
        return messages.count()

    @database_sync_to_async
    def get_conversation(self, conversation_id):
        return Conversation.objects.get(id=conversation_id)

    @database_sync_to_async
    def get_other_participant(self, conversation):
        return conversation.get_other_participant(self.user_profile)

def send_notification(user_id, notification_type, message, data=None):
    """Helper function to send notifications"""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            'type': 'send_notification',
            'type': notification_type,
            'message': message,
            'data': data or {}
        }
    ) 