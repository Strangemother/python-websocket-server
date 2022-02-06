from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import json

from . import devices

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
        raise NotImplemented()

    def is_json(self):
        m = self.message
        return len(m) > 1 and (m[0] == '{' and m[-1] == '}')

    def __str__(self):
        return f"Packet({self.uuid}): {self['as']} {self['event']}"


class ConnectionManager(object):

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.uuid_counter = 0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def receive_text(self, message: str, sender: WebSocket):
        """Direct input from the socket, farm to owner and continue.
        return a continue 1 or STOP 0
        """
        packet = await self.convert_message(message, sender)
        await self.digest_packet(packet)
        # await self.broadcast(f"In: {message}")
        return 1

    async def receive_binary(self, message: bytes, sender: WebSocket):
        """Direct input from the socket, farm to owner and continue.
        return a continue 1 or STOP 0
        """
        packet = await self.convert_message(message, sender)
        await self.digest_packet(packet)
        # await self.broadcast(f"In: {message}")
        return 1

    async def convert_message(self, message: str, websocket:WebSocket):
        self.uuid_counter+=1

        return Packet(message, websocket, uuid=self.uuid_counter)

    async def digest_packet(self, packet: Packet):
        """Given a system converted message to Package type,
        digest and iterate into the framework
        """
        pass


class PacketManager(ConnectionManager):
    # await host.send_personal_message(f"You wrote: {data}", websocket)
    # await host.broadcast(f"Client #{client_id} says: {data}")

    def __init__(self):
        super().__init__()
        self.devices = ()

    async def mount(self):
        units = (
            devices.Mouse,
            devices.Keyboard,
            )
        for unit in units:
            await self.mount_unit(unit)

    async def mount_unit(self, device_class):
        dev = device_class()

        self.devices += (dev,)


    async def digest_packet(self, packet: Packet):
        for device in self.devices:
            await device.read_packet(packet)
        # else:
        #     print('Incoming packet', packet)



Host = PacketManager
