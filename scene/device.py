from fastapi import WebSocket
from manager import Packet, Device
from collections import defaultdict
from message import easy_send


import register


def is_world(packet:Packet, word='world', key='unit'):
    entity_is = packet.message

    if packet.is_json():
        entity_is =packet.get_json().get(key, None)

    return (entity_is or '').lower() == word


class SceneManager(Device):
    """The scene manager mounts the incoming "device" list to detect "world"
    packages.
    """
    scenes = None

    def __init__(self):
        self.scenes = self.scenes or {}
        self.socket_scene_list = defaultdict(set)

    async def digest_packet(self, packet: Packet):
        """Check if the scene sent this message.
        """
        if is_world(packet):
            print('New Scene\n')
            await self.stack_scene(packet)

        print('SceneManager, digest_packet')

    async def disconnect(self, websocket):
        print('SceneManager::disconnect')

        deleted = await self.drop_scene_owner(websocket.uuid)
        deleted_res = register.delete_scenes(*deleted)
        await self.host.broadcast_json(_exclude=(websocket,),
            event='scenes_disconnect',
            action='disconnect',
            type='scenes',
            deleted=tuple(x for x,y in deleted_res.items() if y is True)
        )

    async def stack_scene(self, packet: Packet):
        """A new scene:
            {"new_network":1257,"root":1179,"is":"World"}
        """
        # content = packet.as_json()
        ## int ID of the scene
        # iid = content.get('root')

        """Convert the incoming JSON packet to an internal event model
        """
        new_scene = packet.as_event('NewScene')
        # int ID of the scene
        iid = new_scene.root

        if iid in self.scenes:
            return await self.reconnect_scene(iid, packet)
        await self.connect_scene(iid, packet)
        #await self.announce_scene(iid, packet)

    async def reconnect_scene(self, iid, packet):
        print('Reattach existing scene')
        return await self.connect_scene(iid, packet,
                                        count=self.scenes[iid]['count']+1)

    # async def announce_scene(self, iid, packet):
    #     msg_dict = packet.get_json()
    #     print('Announcing', packet.message)
    #     await self.host.broadcast(packet.message, exclude=(packet.owner,))

    async def connect_scene(self, iid, packet, **extra):
        """Append the scene to the existing list of manages scenes.
        """
        entry = packet.get_json()
        entry['count'] = 0
        entry['owner'] = tuple(packet.owner.client)
        entry['uuid'] = packet.owner.uuid
        entry.update(extra)

        await self.add_scene_owner(packet.owner.uuid, iid)
        self.scenes[iid] = entry
        register.add_scene(iid, entry)

    async def drop_scene_owner(self, uuid):
        deletes = set()
        if uuid in self.socket_scene_list:
            print('deleting scenes', uuid, self.socket_scene_list[uuid])
            deletes.update(self.socket_scene_list[uuid])
            del self.socket_scene_list[uuid]

        return tuple(deletes)

    async def add_scene_owner(self,uuid, root_id):
        print('add_scene_owner', uuid, root_id)
        self.socket_scene_list[uuid].add(root_id)

