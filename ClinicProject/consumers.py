import json
from channels.generic.websocket import AsyncWebsocketConsumer

class QueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.doctor_id = self.scope['url_route']['kwargs']['doctor_id']
        self.queue_group_name = f'queue_updates_{self.doctor_id}'

        await self.channel_layer.group_add(
            self.queue_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.queue_group_name,
            self.channel_name
        )

    async def queue_update(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))