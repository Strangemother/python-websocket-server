"""A Central hub for applications, scenes, and client instance connections.
The register acts as a reversable graph, connecting a client to one or more scenes.

When an event occurs from a scene, the SceneManager transmits the events to the
target clients. in-game components are owned by clients, therefore some elements
should only route to unique clients.



"""

from collections import defaultdict
from device import Device

ERROR = {}

class RegisterEntity(object):


    def __init__(self, *a, **kw):
        self.kw = kw

    def get_socket(self):
        """
        return the bound socket if it exists.
        """
        try:
            return client_references[self.uuid]
        except KeyError:
            raise NoClient(self.uuid)

    def update(self, *a, **kw):
        print('Update', self.__class__.__name__, a, kw)
        self.kw.update(*a, **kw)

    def repr_str(self):
        return f"{self.kw}"

    def __repr__(self):
        return f'<{self.__class__.__name__}: {tuple(self.kw.keys())} "{self.repr_str()}">'

    def __getattr__(self, key):
        return self.kw[key]

import weakref

client_references = weakref.WeakValueDictionary()


class RegisterManager(Device):


    async def connect_accept(self, websocket):
        client_references[websocket.uuid] = websocket
        print('register::RegisterManager::connect_accept')

    async def disconnect(self, websocket):
        try:
            client_references.pop(websocket.uuid)# = websocket
        except KeyError:
            print('No user to pop', websocket.uuid)
        print('register::RegisterManager::disconnect')


class SceneRegister(RegisterEntity):

    def repr_str(self):
        return f'{self.root}'

    def __int__(self):
        return self.root


class NoClient(Exception):
    pass


class ClientRegister(RegisterEntity):

    def repr_str(self):
        return f'{self.uuid}'


    def __int__(self):
        return self.uuid

    def __eq__(self, other):
        if isinstance(other, (int, float)):
            return self.uuid == other

        return super().__eq__(other)

scenes = defaultdict(SceneRegister)
clients = defaultdict(ClientRegister)


def add_scene(rid, scene_data):
    print('store scene', rid, scene_data)
    scenes[rid].update(scene_data)
    return rid in scenes


def get_scenes(scenes_uuids, default=ERROR):
    """Return a client by the UUID. Id the client exists, return the client data.
    """
    scenes_res = ()
    for uuid in scenes_uuids:
        if uuid in scenes:
            scenes_res += (scenes[uuid], )
    return scenes_res


def delete_scenes(*rids):
    res = {}
    for rid in rids:
        res[rid] = delete_scene(rid) is not None

    return res

def delete_scene(rid):
    try:
        v = scenes.pop(rid)
        print('register::delete_scene', rid, '==', v)
        return v
    except KeyError as err:
        print('Did not delete scene', rid, 'from', scenes)
        return None
    return rid


def scene_list():
    return tuple(scenes.keys())


def add_client(rid, client_data):
    print('store client', rid, client_data)
    clients[rid].update(client_data)
    return rid in clients

def client_list():
    return tuple(clients.keys())


def get_client(uuid, default=ERROR):
    """Return a client by the UUID. Id the client exists, return the client data.
    """
    if uuid in clients:
        return clients[uuid]
    if default is ERROR:
        raise KeyError(f"no key {uuid}")
    return default
