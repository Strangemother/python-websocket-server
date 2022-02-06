"""The house connection manager handles inbound connections for _first_ auth.
Then moves the connection into a lobby once authed.
"""
from fastapi import WebSocket, WebSocketDisconnect
from .. import exceptions, state
from .auth import blacklist


class Forever(state.MicroState):
    async def concurrent(self, data, owner, micro_position):
        print('F:', data)

        return False, True


class Debug(state.KeyMicroState):

    name = 'debug'

    async def push_state_message(self, micro_position, data, owner):
        move_on = False
        micro_val = 2
        import pdb; pdb.set_trace()  # breakpoint 72df0baa //

        return move_on, micro_val


class HotMove(state.KeyMicroState):

    async def push_state_message(self, micro_position, data, owner):
        t = data.get('text', None)
        if t == self.kwargs.get('text'):
            self.release()

        # move_on, micro_position inc
        return False, True

# These plugins define the procedural list a single client should
# walk. Each step is like a function - but built with an async waiting.
plugins = (
    state.MicroState(name='BEFORE'),
    state.KeyMicroState(name='beta', move_to='other', init_value=-3),
    state.KeyLobby(name='keyarea',
        # state_index=0,
        acceptors=(
            state.MicroState(name='egg'),
            HotMove(name='fred', text='egg', move_to='cake'),
            state.KeyMicroState(name='beta', move_to='delta', init_value=-3),
            state.MicroState(name='charlie'),
            state.KeyMicroState(name='delta', move_to='charlie'),
            state.KeyMicroState(name='cake', move_to='debug'),
            Debug(),
        )
     ),
    state.KeyMicroState(name='other', move_to='keyarea', init_value=1),
    state.Lobby(name='area',
        # state_index=0,
        acceptors=(
            Forever(name='FOREVER'),
        )
     ),
)

state_machine = state.StateMachine(plugins,
        entry_acceptors=(
            state.MicroState(name='alpha'),
            state.MicroState(name='beta'),
        )
    )

# blacklist.add('127.0.0.1')

## A list of acceptance modules.
ACCEPT_PLUGINS = (
        # hard_blacklist,
        blacklist.hard_error_blacklist,
    )



async def can_accept_socket(websocket):
    """Given a websocket, run through the accept phase to ensure all pre-auth steps
    are true
    """
    for plugin in ACCEPT_PLUGINS:
        func = plugin.accept_socket if hasattr(plugin, 'accept_socket') else plugin
        res = await func(websocket)
        if res is False:
            return False

    return True



class Manager(object):
    """The input manager handles ingress and drops of all docket connections,
    farmed from the host wsgi function into `master_ingress(websocket)`.
    A prepared socket is pushed into a async wait loop until a disconnect occurs.

    To use the manager, create a new instance and call the master_ingress or
    `uuid_ingress` function to initiate a flow on the socket:

        con_manager = connection.Manager(app)
        await con_manager.mount()
        await con_manager.master_ingress(websocket)

    The host calling these functions doesn't care about the rest - of which
    is handled within this manager or the referenced `state_machine`.
    """
    def __init__(self, app):

        print('connection.Manager', app)

    async def mount(self):
        """mount the manager as the (FastAPI) interface is loaded.
        """
        print('async Manager.mount')

    async def uuid_ingress(self, websocket, uuid):
        """The websocket attached through a uuid named socket.
        Check for the existence of the uuid and statify.
        """
        # client_id = id(websocket)
        websocket.client_uuid = uuid
        await self.master_ingress(websocket)#, uuid)

    async def master_ingress(self, websocket):
        """The websocket came through the main / endpoint -
        designated unsafe until moved into a safe lobby.
        """
        allow_continue, err = await self.run_entry(websocket)
        if allow_continue:
            err = await self.loop_wait(websocket)

        client_id = id(websocket)
        print(f'Signal close receive of {client_id}: Error: {err}')
        await self.disconnect_socket(websocket, client_id, err)

    async def run_entry(self, websocket):
        """Perform the initial entry before the socket is pushed into the
        wait look. Call initial entry and capture any faults

        Return a tuple of (bool, err) for success. If the success bool is true
        the error is none.
        """
        err = None
        allow_continue = False
        try:
            allow_continue = await self.initial_entry(websocket)

        except exceptions.EntryException as error:
            allow_continue = False
            err = error

        return (allow_continue, err)

    async def initial_entry(self, websocket):
        """The new websocket is requesting access to the network
        perform an accept() and return the state of the acceptance.

        If False is returned the websocket will drop regardless of the
        accept() state.
        """
        chain_res = await can_accept_socket(websocket)
        if chain_res:
            await websocket.accept()
            try:
                await state_machine.initial_entry(websocket)
            except state.Done:
                print('\n!The state machine resolved Done at entry...')
        return chain_res

    async def loop_wait(self, websocket):
        """With the initial entry for websocket complete, step into a
        forever loop, waiting on content from the receive() method.
        """
        error = None
        allow_continue = 1
        try:
            while allow_continue:
                if websocket.client_state.value == 0: break

                data = await websocket.receive()
                allow_continue = await self.receive(data, websocket)
                # print('-> allow_continue', allow_continue)
        except WebSocketDisconnect as err:
            print('Client disconnect', err)
            error = err
            # await self.disconnect_socket(websocket, client_id)
        return error

    async def receive(self, data, websocket):
        """Data recieved from the client. Process and return a continue
        bool.
        """
        return await state_machine.push_message(data, websocket)

    async def disconnect_socket(self, websocket, client_id=None, error=None):
        """Called automatically or requested through the API to _disconnect_
        the target websocket by sending a close 1000 event.
        """
        await state_machine.disconnecting_socket(websocket, client_id, error)
        await websocket.close(code=1000)#'I dont wantyou')


