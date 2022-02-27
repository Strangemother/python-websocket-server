from fastapi import WebSocket
from manager import Packet, Device
from message import easy_send
# from message import easy_send

import register

from collections import defaultdict


class PipeManager(Device):
    """Bridge the data from Client to server.
    """
    clients = None

    def __init__(self):
        self.clients = self.clients or defaultdict(set)

    async def digest_packet(self, packet: Packet):
        """Check if the client sent this message.
        """
        content = packet.as_json()
        action = content.get('action', None)
        client = content.get('client', None)
        method_name = f'action_{action}'.lower()
        return await getattr(self, method_name)(packet)

    async def action_none(self, packet:Packet):
        print('Pipes. Bad or no action', packet.as_json())

    async def action_create(self, packet:Packet):
        """
        Receive a create command from the client, to invent an entity within
        the view and assign ownership to the target client.
        """
        print('\nPipes::Create unit')
        ok, owner_client, target_client = await self.get_client_pair(packet)
        if ok is False:
            owner_uuid = packet.owner.uuid
            print(f'Create stopped early. ok:, {ok}: "{owner_uuid}"')
            resp = await packet.respond_json(
                event='create_fail',
                reason=f"Client targeting returned false: {owner_client}",
                provider_uuid=owner_uuid,
            )

            return

        return await self.generate_unit(packet, target_client)

    async def generate_unit(self, packet:Packet, target_client):
        # if target client uuid has the scene ID, allow the unit to generate.
        content = packet.as_json()
        target_scenes = content.get('scenes', ())

        scenes = self.get_registered_scenes(target_client.uuid, target_scenes)
        print('Creaing unit.', content.get('entity'), 'in', scenes, 'for', target_client)

        # send the message to the scene, expecting a "response"
        # announce to the client "create" will occur
        # store response.rid to the client.uuid
        # Any messages are piped through the users.
        scene_sockets = tuple(x.get_socket() for x in scenes)
        await easy_send(to=scene_sockets, _owner=target_client.uuid, **content)


    def get_registered_scenes(self, uuid, scene_ids):
        """Given a client UUID (the unique websocket ID) and the list of scene IDs
        return a list of SceneRegister applicable for the client id.

            self.get_registered_scenes(target_client.uuid, (1179, 1140,))
            (<SceneRegister>, ...)
        """

        # Get all the scenes the client is allowed to view. The 'uuid' is a unique
        # value applied to the websocket instance when created.
        client_scenes = self.clients[uuid]
        # Gather a unique list of all available scenes, and intersect with the
        # user given list.
        target_scenes = set(scene_ids)
        avail_scenes = target_scenes.intersection(set(int(x) for x in client_scenes))

        reg_scenes = register.get_scenes(avail_scenes)
        return reg_scenes


    async def get_client_pair(self, packet:Packet):
        """Return a tuple of gathered clients, owner (the socket providing the message) and
        target (the socket assigned for this packet).

            ok, owner_client, target_client

        if `ok` is false, arg [1] (owner_client) is the error. with the target_client
        as None.

        This is useful for extracting the pair for the coms,
        """
        content = packet.as_json()
        owner_uuid = packet.owner.uuid

        print('PipeManager::get_client_pair', owner_uuid, content)

        owner_client = register.get_client(owner_uuid, None)

        if owner_client is None:
            #send error message, to ask for client register event.
            print('bad owner id. socket must be registered as a client')
            resp = await packet.respond_json(
                event='bind_fail',
                reason="Unknown provider_uuid. The Owner must be a registered client.",
                provider_uuid=owner_uuid,
            )

            return False, resp, None

        client_id = content.get('client', owner_client)
        target_client = owner_client

        if client_id != owner_uuid:
            print('Finding client', client_id)
            target_client = register.get_client(owner_client, None)
            print('target_client', target_client)

        if target_client is None:
            m = f'Cannot bind a none client. Choices are: {register.client_list()}'
            print(m)
            # return client choice error event.
            return False, m, None

        return True, owner_client, target_client

    async def action_bind(self, packet:Packet):
        """Bind a client to one or more _items_. If the item binds return
        a success message, else return a failure.

            {'action': 'bind', 'client': 67856816, 'scenes': [1179]}

        """
        content = packet.as_json()
        ok, owner_client, target_client = await self.get_client_pair(packet)

        if ok is False:
            print('Cannot Bind', owner_client)
            return

        scene_ids = content.get('scenes', None)
        scenes = register.get_scenes(scene_ids)

        msg = dict(
            event='bind_accept',
            client_uuid=int(target_client),
            provider_uuid=int(owner_client),
            scenes=tuple(int(x) for x in scenes),
        )

        if is_empty(scenes):
            print('No scenes.')
            msg.update(event='bind_fail',
                       reason='No scenes given',)

            # return await packet.respond_json(
            #     # event='bind_fail',
            #     # reason='No scenes given',
            #     # client_uuid=int(target_client),
            #     # provider_uuid=int(owner_client),
            #     # scenes=tuple(int(x) for x in scenes),
            #     )

        print('Bind client', target_client, 'to', scenes, ' - by', owner_client)

        self.clients[target_client.uuid].update(set(scenes))

        return await packet.respond_json(**msg)

            # event='bind_accept',
            # client_uuid=int(target_client),
            # provider_uuid=int(owner_client),
            # scenes=tuple(int(x) for x in scenes),
            # )


def is_empty(scenes):
    return scenes is None or len(scenes) == 0
