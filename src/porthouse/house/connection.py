"""The house connection manager handles inbound connections for _first_ auth.
Then moves the connection into a lobby once authed.
"""
from fastapi import WebSocket, WebSocketDisconnect
from .. import exceptions, state
from .auth import blacklist

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

MANAGERS = {}

def get_manager_by_id(mid):
    return MANAGERS[mid]


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
    clients = None

    def __init__(self, state_machine):
        MANAGERS[id(self)] = self
        print('connection.Manager', state_machine)
        self.clients = {}

        state_machine.manager_id = id(self)
        self.state_machine = state_machine


    def get_clients(self):
        # return tuple(self.clients.keys())
        return self.clients

    async def mount(self):
        """mount the manager as the (FastAPI) interface is loaded.
        """
        print('async Manager.mount')
        await self.state_machine.mount()

    async def uuid_ingress(self, websocket, uuid):
        """The websocket attached through a uuid named socket.
        Check for the existence of the uuid and statify.
        """
        # client_id = id(websocket)
        websocket.client_uuid = uuid
        await self.master_ingress(websocket)#, uuid)

    async def service_ingress(self, websocket, **options):
        return await self.master_ingress(websocket, **options)

    async def master_ingress(self, websocket, **options):
        """The websocket came through the main / endpoint -
        designated unsafe until moved into a safe lobby.
        """
        websocket.set_init_options(options)
        allow_continue, err = await self.run_entry(websocket)
        if allow_continue:
            err = await self.loop_wait(websocket)

        client_id = id(websocket)
        print(f'Manager.master_ingress: Signal close receive of {client_id}: Error: {err}')
        await self.disconnect_socket(websocket, None, err)

    async def run_entry(self, websocket):
        """Perform the initial entry before the socket is pushed into the
        wait look. Call initial entry and capture any faults

        Return a tuple of (bool, err) for success. If the success bool is true
        the error is none.
        """
        error = None
        try:
            allow_continue = await self.initial_entry(websocket)
        except exceptions.EntryException as err:
            allow_continue = False
            error = err
        return (allow_continue, error)

    async def initial_entry(self, websocket):
        """Called by `self.run_entry()` with the new socket - of which needs
        accepting.

        The new websocket is requesting access to the network perform an
        accept() and return the state of the acceptance.

        If False is returned the websocket will drop regardless of the
        accept() state.
        """
        chain_res = await can_accept_socket(websocket)
        can_accept = False

        if chain_res:
            try:
                can_accept = await self.state_machine.initial_entry(websocket)
            except state.Done as err:
                can_accept = err.args[0]
                print('\n!The state machine resolved Done at entry. Keep open ==', can_accept)

            if can_accept:
                # print('\n\nconnection.Manager.first_mount\n\n')
                # websocket.first_mount(self)
                await websocket.accept()
                # websocket._manager = self
                await self.append_client(websocket)
                await self.state_machine.accepted(websocket)
            else:
                print('Initial Entry did not accept socket.', websocket)

        return chain_res

    async def append_client(self, websocket):
        self.clients[websocket.get_id()] = websocket

    async def remove_client(self, websocket):
        del self.clients[websocket.get_id()]

    async def loop_wait(self, websocket):
        """With the initial entry for websocket complete, step into a
        forever loop, waiting on content from the receive() method.
        """
        try:
            error = await self._while_allow_continue(websocket)
        except WebSocketDisconnect as err:
            print('connection.Manager.loop_wait: Client disconnect:', err)
            error = err
            # await self.disconnect_socket(websocket, client_id)
        return error

    async def _while_allow_continue(self, websocket):
        """Wait forever upon the websocket.receive(). Call to `self.receive`
        with incoming data packets.

        If the intern receive call returns False, the loop will close -
        disconnecting the client.
        """
        allow_continue = 1
        error = None

        while allow_continue:

            if websocket.client_state.value == 1:
                data = await websocket.receive()
                allow_continue = await self.receive(data, websocket)
                continue

            # The if statement failed; the client is 0 or 2
            error = 'connection.Manager: Disconnect by client'

            if websocket.client_state.value == 2:
                # The client disonnected with a 'close'
                print(f'\nManager._while_allow_continue disconnect announced: {error}\n')

            ## We could raise a disconnect, with a custom message
            ## or inherited.
            raise WebSocketDisconnect(error) # from err

            ## Or we could return with an error entity,
            # return error

            ## Or Regardless of the return or raise, we can simply kill the
            ## loop, and fill the error string
            allow_continue = 0

        return error

    async def receive(self, data, websocket):
        """Data recieved from the client. Process and return a continue
        bool.
        """
        return await self.state_machine.push_message(data, websocket)

    async def disconnect_socket(self, websocket, client_id=None, error=None):
        """Called automatically or requested through the API to _disconnect_
        the target websocket by sending a close 1000 event.
        """
        await self.state_machine.disconnecting_socket(websocket, client_id, error)
        await self.remove_client(websocket)
        await websocket.close(code=1000)#'I dont wantyou')

