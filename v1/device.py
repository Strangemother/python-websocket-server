from packet import Packet
from message import easy_send
from fastapi import WebSocket


class Device(object):

    host = None

    async def add_host(self, host):
        self.host = host

    async def receive_text(self, message: str, sender: WebSocket):
        pass

    async def receive_binary(self, chunk: bytes, sender: WebSocket):
        pass

    async def digest_packet(self, packet: Packet):
        """Check if the scene sent this message.
        """
        pass

    async def connect_accept(self, websocket:WebSocket):
        pass

    async def disconnect(self, websocket:WebSocket):
        pass

    async def respond_json(self, to, **content):

        if isinstance(to, Packet):
            to = to.owner

        return await easy_send(to=to,
                **content
            )

