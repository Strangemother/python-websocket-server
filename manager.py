from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import json

class Packet(object):
    """A message from external converted to an internal message, ready for
    digest through the waiting components.
    """

    def __init__(self, message: str, owner: WebSocket, uuid:None):
        self.message = message
        self.owner = owner
        self.json = None
        self.uuid = uuid

    def get_json(self):
        if self.json is None:
            self.json = self.convert()
        return self.json

    def convert(self):
        """Convert the internal message to the dict format for application
        digest.
        """
        if self.is_json():
            return self._from_json()
        return self._from_text()

    def __getitem__(self, k):
        return self.convert().get(k)

    def _from_json(self):
        return json.loads(self.message)

    def _from_text(self):
        """Convert the special packet into a json dict.
        """
        # raise NotImplemented()
        return {"text": self.message}

    def is_json(self):
        m = self.message
        return len(m) > 1 and (m[0] == '{' and m[-1] == '}')

    def __str__(self):
        return f"Packet({self.uuid}): {self.message}"


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
        self.disconnect(websocket)

    async def connect(self, websocket: WebSocket):
        print('--- ConnectionManager::connect (websocket.accept)')
        await websocket.accept()
        self.active_connections.append(websocket)
        return 1

    def disconnect(self, websocket: WebSocket):
        print('Forget', websocket)
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, exclude=None):
        exclude = exclude or ()
        print('ConnectionManager broadcast to', message)
        for websocket in self.active_connections:
            if websocket in exclude:
                continue
            await websocket.send_text(message)

    async def receive_text(self, message: str, sender: WebSocket):
        """Direct input from the socket, farm to owner and continue.
        return a continue 1 or STOP 0
        """
        print('ConnectionManager Accept packet')
        packet = await self.convert_message(message, sender)
        print('ConnectionManager digest packet:', packet)
        await self.digest_packet(packet)
        return 1

    async def receive_binary(self, chunk: bytes, sender: WebSocket):
        """Direct input from the socket, farm to owner and continue.
        return a continue 1 or STOP 0
        """
        print('ConnectionManager Accept binary chunk')
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
        await self.broadcast(packet.message, exclude=(packet.owner,))


class PacketManager(ConnectionManager):
    # await host.send_personal_message(f"You wrote: {data}", websocket)
    # await host.broadcast(f"Client #{client_id} says: {data}")

    def __init__(self):
        print('New PacketManager')
        super().__init__()
        self.devices = ()

    async def mount(self):
        print('Host Mount')
        units = ()
        for unit in units:
            await self.mount_unit(unit)

    async def mount_unit(self, device_class):
        dev = device_class()
        self.devices += (dev,)


Host = PacketManager
