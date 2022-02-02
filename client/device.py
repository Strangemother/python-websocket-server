from fastapi import WebSocket
from manager import Packet, Device
from message import easy_send

import register


def is_client(packet:Packet, word='client', key='unit'):
    entity_is = packet.message

    if packet.is_json():
        entity_is =packet.get_json().get(key, None)

    return (entity_is or '').lower() == word


class ClientManager(Device):
    """The client manager mounts the incoming "device" list to detect "client"
    packages.
    """
    clients = None

    def __init__(self):
        self.clients = self.clients or {}

    async def digest_packet(self, packet: Packet):
        """Check if the client sent this message.
        """
        if is_client(packet):
            print('New Client\n')
            await self.stack_client(packet)

        print('ClientManager, digest_packet')

    async def stack_client(self, packet: Packet):
        """A new client:
            {"new_network":1257,"root":1179,"is":"World"}
        """
        # content = packet.as_json()
        ## int ID of the client
        # iid = content.get('root')

        """Convert the incoming JSON packet to an internal event model
        """
        new_client = packet.as_event('NewClient')
        # int ID of the client
        iid = new_client.owner

        if iid in self.clients:
            return await self.reconnect_client(iid, packet)
        await self.connect_client(iid, packet)
        #await self.announce_client(iid, packet)

    async def reconnect_client(self, iid, packet):
        print('Reattach existing client')
        return await self.connect_client(iid, packet,
                                        count=self.clients[iid]['count']+1)

    async def connect_client(self, iid, packet, **extra):
        """Append the client to the existing list of manages clients.
        """
        entry = packet.get_json()
        entry['count'] = 0
        entry['owner'] = tuple(packet.owner.client)
        entry['uuid'] = packet.owner.uuid
        entry.update(extra)

        self.clients[iid] = entry
        stored = register.add_client(iid, entry)
        await self.send_welcome_pack(packet)

    async def send_welcome_pack(self, packet):
        """Send a "first response to the client"
        """
        await easy_send(to=packet.owner,
                event='welcome',
                friendly='Howdy.',
                nominated='client',
                id=packet.owner.uuid,
                scenes=register.scene_list())
