from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import json
from functools import lru_cache
import events
from packet import Packet
from message import easy_send
from device import Device

class ConnectionManager(object):

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.uuid_counter = 0

    async def accept_socket(self, websocket, client_id):
        print('Accepting socket')
        # await websocket.accept()
        allow_continue = await self.connect(websocket)

        try:
            while allow_continue:
                if websocket.client_state.value == 0:
                    break

                data = await websocket.receive()
                allow_continue = await self.receive(data, websocket)

                if allow_continue == 1:
                    continue

                print(f'Signal close receive of {client_id}')
                await self.disconnect_socket(websocket, client_id)
        except WebSocketDisconnect as err:
            print('Client disconnect', err)
            await self.disconnect_socket(websocket, client_id)

    async def disconnect_socket(self, websocket, client_id):
        await self.broadcast(f"Client #{client_id} left the chat",
            exclude=(websocket,))
        await self.disconnect(websocket)

    async def connect(self, websocket: WebSocket):
        print('--- ConnectionManager::connect (websocket.accept)')
        websocket.uuid = id(websocket)
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.all_devices('connect_accept', websocket)

        return 1

    async def disconnect(self, websocket: WebSocket):
        print('Forget', websocket)
        self.active_connections.remove(websocket)
        await self.all_devices('disconnect', websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, exclude=None):
        exclude = exclude or ()
        print('ConnectionManager broadcast to', message)
        for websocket in self.active_connections:
            if websocket in exclude:
                continue
            await websocket.send_text(message)

    async def broadcast_json(self, _exclude=None, **content):
        exclude = _exclude or ()
        print('ConnectionManager broadcast JSON to')
        for websocket in self.active_connections:
            if websocket in exclude:
                continue
            await websocket.send_json(content)

    async def receive_text(self, message: str, sender: WebSocket):
        """Direct input from the socket, farm to owner and continue.
        return a continue 1 or STOP 0
        """
        return await self.general_message(message, sender)

    async def receive_binary(self, chunk: bytes, sender: WebSocket):
        """Direct input from the socket, farm to owner and continue.
        return a continue 1 or STOP 0
        """
        print('ConnectionManager Accept binary chunk')
        return await self.general_message(chunk.decode('utf'), sender)

    async def general_message(self, message, sender:WebSocket):
        packet = await self.convert_message(message, sender)
        print('ConnectionManager general_message:', packet)
        await self.digest_packet(packet)
        return 1

    async def receive(self, event: dict, sender: WebSocket):
        """Direct input from the socket, farm to owner and continue.
        return a continue 1 or STOP 0
        """

        if event['type'] == 'websocket.disconnect':
            return 0

        print('ConnectionManager receive', event)
        if 'text' in event:
            return await self.receive_text(event['text'], sender)

        if 'bytes' in event:
            return await self.receive_binary(event['bytes'], sender)

        return 1

    async def convert_message(self, message: str, websocket:WebSocket):
        self.uuid_counter+=1
        return Packet(message, websocket, uuid=self.uuid_counter)

    async def digest_packet(self, packet: Packet):
        """Given a system converted message to Package type,
        digest and iterate into the framework
        """
        print('ConnectionManager digest:', packet, 'and broadcast')
        await self.all_devices('digest_packet', packet)
        # await self.broadcast(packet.message, exclude=(packet.owner,))

    async def all_devices(self, method_name, *a, **kw):
        for device in self.devices:
            print('Run', device, method_name, a, kw)
            await getattr(device, method_name)(*a, **kw)


class PacketManager(ConnectionManager):
    # await host.send_personal_message(f"You wrote: {data}", websocket)
    # await host.broadcast(f"Client #{client_id} says: {data}")

    units = None
    devices = None
    def __init__(self, devices=None):
        print('New PacketManager')
        super().__init__()
        self.units = devices or ()
        self.devices= ()

    async def mount(self):
        print('Host Mount')
        for unit in self.units or ():
            await self.mount_unit(unit)

    async def mount_unit(self, device_class):
        dev = device_class()
        await dev.add_host(self)
        self.devices += (dev,)


Host = PacketManager


class BroadcastDevice(Device):

    async def digest_packet(self, packet: Packet):
        print('BroadcastDevice digest:', packet, 'and broadcast')
        await self.host.broadcast(packet.message, exclude=(packet.owner,))

