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
    def __init__(self, state_machine):
        print('connection.Manager', state_machine)
        self.state_machine = state_machine

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
        error = None
        try:
            allow_continue = await self.initial_entry(websocket)
        except exceptions.EntryException as err:
            allow_continue = False
            error = err
        return (allow_continue, error)

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
                await self.state_machine.initial_entry(websocket)
            except state.Done:
                print('\n!The state machine resolved Done at entry...')
        return chain_res

    async def loop_wait(self, websocket):
        """With the initial entry for websocket complete, step into a
        forever loop, waiting on content from the receive() method.
        """
        try:
            error = await self._while_allow_continue(websocket)
        except WebSocketDisconnect as err:
            print('Client disconnect:', err)
            error = err
            # await self.disconnect_socket(websocket, client_id)
        return error

    async def _while_allow_continue(self, websocket):
        allow_continue = 1
        error = None

        while allow_continue:

            if websocket.client_state.value == 1:
                data = await websocket.receive()
                allow_continue = await self.receive(data, websocket)
                continue

            # The if statement failed; the client is 0 or 2
            error = 'Disconnect by client'

            if websocket.client_state.value == 2:
                # The client disonnected with a 'close'
                print(f'\n{error}\n')

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
        await websocket.close(code=1000)#'I dont wantyou')


