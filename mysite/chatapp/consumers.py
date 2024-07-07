from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from .models import ChatMessage, ChatRoom


class ChatConsumer(AsyncJsonWebsocketConsumer):
    
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        
        # code to connect to a particular room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        # now we have a channel layer and group inside of it
        await self.accept()
        
    async def disconnect(self):
        await self.channel_layer.group_discard(
            self.channel_layer,
            self.room_group_name
        )
    
    # receiving the message sent to socket from front-end (room.html)
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']
        room = data['room']
        # now we need to send this message to the channel layer
        # we have the group in channel layer
        await self.channel_layer.group_send(
            self.room_group_name,{
                'type':'chat_message',
                'message':message,
                'username':username,
                'room':room,
            }
        )
        
        # calling save function to save the received message
        await self.save_message(username, room, message)
        
        # once the message is sent to channel layer, we also need to send it to room as well
    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        room = event['room']
        
        await self.send(text_data=json.dumps({
            'message':message,
            'username':username,
            'room':room,
        }))
        
        # now that we have sent the message to client
        # now we need to go back to front-end to receive the message as well

# to save all the messages
    @sync_to_async #this is a synchronous fn so we use 'sync_to_async' decorator
    def save_message(self, username, room, message):
        user = User.objects.get(username=username)
        room = ChatRoom.objects.get(slug=room)  
        ChatMessage.objects.create(user=user, room=room, message_content = message)