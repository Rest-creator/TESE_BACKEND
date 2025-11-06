# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ProductConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.groups = ["products", "services", "supplier_products"] # Add new groups
        for group_name in self.groups:
            await self.channel_layer.group_add(
                group_name,
                self.channel_name
            )
        await self.accept()

    async def disconnect(self, close_code):
        for group_name in self.groups:
            await self.channel_layer.group_discard(
                group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # This consumer is read-only for now, only sending updates.
        # You can add logic here if clients need to send messages (e.g., chat)
        pass

    # Handlers for product updates (from previous context)
    async def product_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'product_update',
            'data': event['data']
        }))

    async def product_delete(self, event):
        await self.send(text_data=json.dumps({
            'type': 'product_delete',
            'data': event['data']
        }))

    # --- New Handlers for Service Updates ---
    async def service_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'service_update',
            'data': event['data']
        }))

    async def service_delete(self, event):
        await self.send(text_data=json.dumps({
            'type': 'service_delete',
            'data': event['data']
        }))

    # --- New Handlers for Supplier Product Updates ---
    async def supplier_product_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'supplier_product_update',
            'data': event['data']
        }))

    async def supplier_product_delete(self, event):
        await self.send(text_data=json.dumps({
            'type': 'supplier_product_delete',
            'data': event['data']
        }))