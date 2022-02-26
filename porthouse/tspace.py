from . import spaces
import typing
from .client import PortWebSocket

# Test space

from collections import defaultdict


class Pipes(object):
    default_room = 'default'

    async def mount(self):
        self.clients = set()
        self.client_assignments = defaultdict(set)
        self.groups = defaultdict(set)

    async def get_target_socket_ids(self, message, websocket):
        # At this point we have a list of unresolved names leading
        # to lists of listening clients.
        # For each name being a channel, client_id - resolve all to _sockets_
        # and push.
        # print('Message in', names)
        # convert rooms to wocket ids
        # drop unused names

        # .. when a socket is open, it binds a uuid to its room,channels
        # the graph is reverse, testing for lists of sockets in a room.
        # the first order, a service pipe may perform subscription changes.
        # every 'manager' registers its clients to the pipe machine.

        names = await self.get_out_channels(message, websocket)
        ids = await self.resolve_channels_to_sockets(names)
        ids = set(ids)
        ids.remove(websocket.get_id())
        return ids

    async def resolve_channels_to_sockets(self, names):
        r = ()
        for name in names:
            # Safely fetch names, unused names don't resolve.
            r  += tuple(x for x in self.groups.get(name, ()))
        return r

    async def get_out_channels(self, message, websocket):
        """Given a message and the owning socket return a list of target channel
        names.
        """
        targets = await self.extract_target_channels(websocket, message)
        channels = await self.get_client_channels(websocket, message)
        services = await self.get_client_service_channels(websocket, message)
        # in iter order
        return services + targets + channels

    async def extract_target_channels(self, websocket: PortWebSocket, message):
        """Return a list of names from the message, in cases where
        the message has a target.
        """
        return ()

    async def get_client_channels(self, websocket: PortWebSocket, message):
        """Given the main socket, return a list
        of client channels
        """
        return (self.default_room, websocket.get_id(),)

    async def get_client_service_channels(self, websocket: PortWebSocket, message):
        """Return a list of service channels, likely forced.
        """
        name_ext = 'service'

        return (
                f'{self.default_room}.{name_ext}',
                f'{websocket.get_id()}.{name_ext}',
            )

    async def connect(self, websocket: PortWebSocket):
        ''' socket connect announcement from the space'''
        _id = websocket.get_id()

        self.clients.add(_id)
        # Add the default space.
        self.add_to_room(_id, self.default_room)

    def add_to_room(self, _id, room):
        # Add a reference to the name.
        self.client_assignments[_id].add(room)
        # We assign a _room_.
        self.groups[room].add(_id)

    async def drop(self, websocket: PortWebSocket):
        ''' socket drop announcement from the space'''
        _id = websocket.get_id()

        # remove the client from all rooms
        for room in self.client_assignments[_id]:
            self.groups[room].remove(_id)

        # remove all assignments
        del self.client_assignments[_id]
        # remove client
        self.clients.remove(_id)

    def remove_from_room(self, _id, room):
        # Add a reference to the name.
        self.client_assignments[_id].remove(room)
        # We assign a _room_.
        self.groups[room].remove(room)


class PipesSpace(spaces.BroadcastLockSpace):
    """A Message in - is piped through the custom messaging."""

    home_state = 'delivery'

    async def message(self, message: typing.Any, websocket: PortWebSocket) -> bool:
        # print('Message from', websocket._client_id, message)
        # Convert the message to an _output_
        d = message._message
        d['type'] = 'websocket.send'

        ids = await self.pipes.get_target_socket_ids(message, websocket)

        for socket in await self.get_clients(ids):
            # if socket is websocket:
            #     continue
            await socket.send(d)

    async def broadcast(self, message: typing.Any, websocket: PortWebSocket):
        for other in await self.get_clients():
            if other is websocket:
                continue
            await other.send(d)

    async def mount(self):
        self.pipes = Pipes()
        await self.pipes.mount()

    async def close(self, err, websocket: PortWebSocket) -> None:
        await self.leave(websocket)
        return await super().close(err, websocket)

    async def close_message(self, data: typing.Any, websocket: PortWebSocket) -> bool:
        await self.leave(websocket)
        return await super().close_message(data, websocket)

    async def leave(self, websocket):
        # print('\n\npipe space heard close')
        await self.pipes.drop(websocket)

    async def connected(self, websocket: PortWebSocket) -> bool:
        # print('\n\npipe space heard connect')
        await self.pipes.connect(websocket)

        return await super().connected(websocket)
