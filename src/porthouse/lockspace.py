"""In version two we couple the movement of a socket into the PortSocket
and utilise a Limbo to position state machine, - acting as managed envionments.

The socket sends communications across the internal channels mesh.
"""
from .client import PortWebSocket

import typing
from . import state, spaces, envelope
from .exceptions import *
from collections import defaultdict
from .house.connection import get_manager_by_id

    # async def disconnecting_socket(self, websocket, client_id, error):
    #     pass


class LockSpaceManager(state.MicroMachine):

    def mount_placements(self):
        # items to run

        self.init_home_state = self.live[0].home_state
        placements = defaultdict(set)

        for lock_space in self.live:
            lock_space.parent = self
            # LR stacked, for parallel calls.
            placements[lock_space.home_state].add(lock_space)

        self.placements = placements

    def resolve_lockspace(self, other):
        if isinstance(other, spaces.LockSpace) is False:
            other = self.placements.get(other, None)
            if other is None:
                # Bad lockspace name,
                raise MissingState(other)
            return other


    async def call_all(self, home_state, method_name, *args, **kwargs) -> bool:

        # Pick placements
        current = self.placements.get(home_state, None)
        if current is None:
            # print('No home_state:', home_state)
            raise MissingState(home_state)

        current = self.placements.get(home_state, None)
        res = ()
        for lock_space in current:
            # for placement_subset in current:
            # for lock_space in placement_subset:
            try:
                v = await getattr(lock_space, method_name)(*args, **kwargs)
                res += (v,)
            except state.Move as err:
                socket, lock_space, other = err.args
                others = self.resolve_lockspace(other)
                print('\nPlugin', lock_space, 'requests move to', others)

                socket.stack_append(tuple(others)[0].home_state)

                for other_lock_space in others:
                    v = await other_lock_space.move_connected(
                            websocket=socket,
                            other=lock_space,
                            method_name=method_name,
                            args=args, kwargs=kwargs)
                    res += (v,)

            except Release as err:
                # Release back up the stack, eseentially releaseto index -1
                socket, lock_space = err.args
                print('\nPlugin', lock_space, 'requests releaseto', others)
                # others = self.resolve_lockspace(other)
                current = socket.stack_release(lock_space.home_state)
                others = self.resolve_lockspace(current)

                for other_lock_space in others:
                    v = await other_lock_space.released_connected(
                            websocket=socket,
                            other=lock_space,
                            method_name=method_name,
                            args=args, kwargs=kwargs)
                    res += (v,)

            except ReleaseTo as err:
                # The plugin has released - moving to the new
                # given state
                socket, lock_space, other = err.args
                others = self.resolve_lockspace(other)
                print('\nPlugin', lock_space, 'requests releaseto', others)
                # Move into 'other'
                socket.stack_replace(tuple(others)[0].home_state)

                for other_lock_space in others:
                    v = await other_lock_space.released_connected(
                            websocket=socket,
                            other=lock_space,
                            method_name=method_name,
                            args=args, kwargs=kwargs)
                    res += (v,)

        return res



class Machine(LockSpaceManager):
    """Inherit the micromachine to action the raw 3
    """
    manager_id = None
    init_home_state = 0

    def __init__(self, envelopes=None, live=None):
        envelopes = envelopes or ()
        self.live = live or ()
        self.funcmap = {
                    'websocket.receive': self.message,
                    'websocket.disconnect': self.close_message,
                }

        self.mount_placements()
        self.envelope = state.EnvelopePlugin(envelopes)

    def get_clients(self):
        return get_manager_by_id(self.manager_id).clients

    async def mount(self):
        for pl in self.live:
            await pl.mount()

    async def initial_entry(self, websocket: PortWebSocket) -> bool:
        # print('\nAssigning envelope\n')
        websocket.envelope = self.envelope
        return websocket.first_mount(self, self.init_home_state)
        # await self.envelope.initial_entry(websocket)
        # return await self.connected(websocket)

    async def accepted(self, websocket: PortWebSocket) -> bool:
        # await self.envelope.initial_entry(websocket)
        return await self.connected(websocket)

    async def connected(self, websocket: PortWebSocket) -> bool:
        # print(self, 'connected')
        res = await self.call_all(websocket.home_state, 'connected', websocket)
        return False not in res

    async def push_message(self, data: typing.Any, websocket: PortWebSocket) -> bool:
        """Called by the connection manager upon a new incoming message.

        Gather and execute the correct mapped function relative to the
        `data.type` - calling method `message` or `close_message`.

        Return the result from either method.
        """
        return await self.funcmap.get(data['type'])(data, websocket)

    async def message(self, data: typing.Any, websocket: PortWebSocket) -> bool:
        """Digest the incoming packet of data.type == 'receive', called by the
        connection manager through `push_message`.

        Run the current home_state message methods.

        return the result from the call_all method.
        """
        # move into the _room_ designated in the socket state data.
        # If the room does not exist, move to Limbo.
        try:
            # data = await websocket.push_message(data)
            res = await self.call_all(websocket.home_state, 'message', data, websocket)
            return False not in res
        except MissingState:
            return False

    async def close_message(self, data: typing.Any, websocket: PortWebSocket) -> bool:

        # move into the _room_ designated in the socket state data.
        # If the room does not exist, move to Limbo.

        # data = await websocket.push_message(data)
        await self.call_all(websocket.home_state, 'close_message', data, websocket)

    async def disconnect_socket(self, websocket: PortWebSocket, client_id=None, error=None):
        return await self.close(error, websocket)

    async def close(self, err, websocket: PortWebSocket) -> None:

        """
        # TODO: Unwind the socket history stack here, calling to
        all _historical_ LockSpaces. Announce to each the closure of this
        socket, allowing scrubbing up through the graph.

        At the moment, this calls the the _current_ home_state.
        """
        await self.call_all(websocket.home_state, 'closed', err, websocket)
