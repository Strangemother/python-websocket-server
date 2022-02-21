import typing

from .exceptions import *
from .client import PortWebSocket


class LockSpace(object):
    """The ability to keep and release a socket.
    """
    home_state = -1

    # the parnet owns the client connections and the data,
    # assigned with the lockspace is made.
    parent = None

    def get_spaces(self):
        """REturn a list of IDS
        """
        return tuple(self.parent.placements.keys())

    async def move_connected(self, websocket, other, method_name:str, args, kwargs):
        """Another Lockspace has released the socket with a move request
        targeting this lockspace. Perform the normal _connection_
        """
        return await self.released_connected(websocket, other, method_name, args, kwargs)

    async def released_connected(self, websocket, other, method_name:str, args, kwargs):
        """Another Lockspace has released the socket with a release request
        targeting this lockspace. Perform the normal _connection_
        """
        print(f'{self}.released_connected from {other} - through {method_name}')
        return await self.connected(websocket)

    async def connected(self, websocket: PortWebSocket) -> bool:
        return await self.keep(websocket)

    async def keep(self, websocket: PortWebSocket) -> bool:
        """Lock the socket into this Lockspace routine, ensuring all future
        packets attend here.
        """
        return

    async def message(self, data: typing.Any, websocket: PortWebSocket) -> bool:
        print(f'{self}.message', data)


    async def close_message(self, data: typing.Any, websocket: PortWebSocket) -> bool:
        """Call this method if a message is type 'disconnect' rather than
        a standard 'message'.
        """
        print(f'{self}.close_message', data)

    async def close(self, err, websocket: PortWebSocket) -> None:
        print(f'{self}.close', err)

    async def release(self, websocket):
        """Release the socket from this space - the next space is defined by
        the machine, being the parent of the socket history_stack
        """
        raise Release(websocket, self)

    async def release_to(self, websocket, name=None):
        """ A _release_ emits a done message with an motion to another
        lockspace.

        This lockspace name is removed from the history, and the
        new name replaces the position -

        Unlike a _move_ of which appends the new release onto the stack, such
        that a _release_ from the "moved to" lockspace returns back-into this
        lockspace.
        """
        raise ReleaseTo(websocket, self, name)

    async def move_to(self, websocket, name=None):
        """Request a Move command, of which transitions the socket to a
        new lockspace, appending the name into the history stack - onced
        resolved this lockspace re-accepts the socket
        """
        # keep_alive, macro, acceptor_pos, internal_pos, _plug = err.args
        #   raise Done(1, plugin, acceptor_pos, internal_pos, self)
        raise state.Move(websocket, self, name)
        # raise Move(1, self, name or self.move_to)

    async def get_clients(self, ids):
        clients = self.parent.get_clients()
        res = ()
        for _id in ids:
            cl = clients.get(_id)
            if cl is None:
                print('Cannot find client', _id)
                continue
            res += (cl, )
        return res

    def __repr__(self):
        s = f'<{self.__class__.__name__}({self.home_state})>'
        return s


class Other(LockSpace):
    home_state = 'other'


class Limbo(LockSpace):
    """If the socket is in a _zero_ state, it's moved into the lobby to persist
    the micro tasks, then moved into the _authed_ area.
    """

    # Designate the _state_ of which to react upon. Zero (0) identifies the
    # _entry_ of a new socket.
    home_state = 0

    async def message(self, data: typing.Any, websocket: PortWebSocket) -> bool:
        print(f'{self}.message', data)
        place = data['text']

        if place in self.get_spaces():
            print('Releasing to', place)
            return await self.release_to(name=place, websocket=websocket)

        print('No Space as name:', place)


class IdentifierLockSpace(LockSpace):
    """Find and implement the user identity. Assign the socket to the
    channel.
    """
    home_state = 'id'

    async def connected(self, websocket: PortWebSocket) -> bool:
        # send welcome. Ask for ID.
        await websocket.send_text('Hello. Please present your ID.')

    async def message(self, data: typing.Any, websocket: PortWebSocket) -> bool:
        if data.text.startswith('id:'):
            _id = data.text[3:].strip()

            print(f'\nID GIVEN: {_id}\n',)
            # TODO: Authing.
            if await self.exists(_id):
                websocket._client_id = _id
                place = 'delivery'
                return await self.release_to(name=place, websocket=websocket)

        print(f'{self}.message', data)

    async def exists(self, name):
        return name in CHANNELS


# Internal Channels, mapping IDS to profiles, and other channels.
CHANNELS = {
    'egg': { 'name': 'Dave' },
    'poppy': { 'name': 'Eric' },
}


class ClientKnowledge(object):
    clients = None

    def add_client(self, websocket):
        # _client_id = websocket._client_id
        socket_id = websocket.get_id()
        self.clients.add(socket_id)


    def get_client_channel_data(self, client_id):
        unit = CHANNELS.get(client_id)
        return unit

    def scrub_client(self, websocket: PortWebSocket) -> None:
        print('\nDelivery room hear closure of', websocket)
        socket_id = websocket.get_id()
        self.clients.remove(socket_id)


class ChannelDeliveryLockSpace(LockSpace, ClientKnowledge):
    """Input messages head to a channel.

    Consider  this a raw message delivery to every connected client.
    The information sent to all sockets, is the same as the content received
    """
    home_state = 'delivery'

    def __init__(self):
        self.clients = set()

    async def get_clients(self, ids=None):
        """Override the parent to return a list of resolved client <sockets>
        using a given list of ids.
        If the ids is None, the internal client list is used (All clients).
        """
        return await super().get_clients(ids or self.clients)

    async def connected(self, websocket: PortWebSocket) -> bool:
        """A new client has entered the lockspace. Send a welcome message
        and store the client ID into the client list.

        Return False to drop the socket.
        """
        _client_id = websocket._client_id
        self.add_client(websocket)

        name = self.get_client_channel_data(_client_id)['name']

        s = ('\nDelivery room received new client '
            f'(#{len(self.clients)}): {_client_id}, {name}\n')
        print(s)

        await websocket.send_text(f'Hello - {name}')

    async def close(self, err, websocket: PortWebSocket) -> None:
        """The client or internal network raised a 'close' event, causing
        the socket to drop from the system.

        Delete any old data no-longer applicable.
        """
        self.scrub_client(websocket)

    async def message(self, message: typing.Any, websocket: PortWebSocket) -> bool:
        print('Message from', websocket._client_id, message)
        # Convert the message to an _output_
        d = message._message
        d['type'] = 'websocket.send'

        for other in await self.get_clients():
            if other is websocket:
                continue

            await other.send(d)

    async def close_message(self, data: typing.Any, websocket: PortWebSocket) -> bool:
        """Call this method if a message is type 'disconnect' rather than
        a standard 'message'.
        """
        print(f'\nChannels heard close with {data}')
        self.scrub_client(websocket)
        print('client count now:', len(self.clients))


class Sibling(LockSpace):

    # Parallel to all other 0 state units.
    home_state = 0
