"""The master websocket client for the application.
This is imported by the ingress.singleton before the FastAPI _app_ is created
"""
from starlette.types import Message#, Receive, Scope, Send
import starlette.websockets # import WebSocket

WebSocketState = starlette.websockets.WebSocketState



class PortWebSocket(starlette.websockets.WebSocket):
    """This WebSocket replaces the application general websocket.
    """
    envelope = None

    # Assigned by the connection manager when the socket enters the system.
    _manager = None

    # Unlike the UUID, the client ID is persistent within the network
    # and a socket must authenticate to resolve a client_id.
    _client_id = None

    # Assigned internal location of the socket.
    # Moved out of the zero state after a release from a micro machine.
    home_state = 0
    history_stack = None

    # Any extra arguments given through set_init_options
    # at point of creation.
    init_options = None

    def get_id(self):
        return id(self)

    async def send(self, message: Message) -> None:
        """Override the starlette.websockets.Websocket.send method to
        iterate any  overrides
        """
        if self.envelope:
            message = await self.envelope.outbound(message, self)
        else:
            print('\nPortwebsoket envelope does not exist')

        await super().send(message)

    async def receive(self) -> Message:
        """Override and _Wait_ for the super receive.
        Return a message unwrapped through the envelope inbound()
        """
        message = await super().receive()

        if self.envelope:
            new_message = await self.envelope.inbound(message, self)
            return new_message
        else:
            print('\nPortwebsoket envelope does not exist.')

        return message

    def set_init_options(self, options):
        self.init_options = options

    def stack_append(self, home_state):
        """Called by a lockstate to store the given str to the placement
        stack any future messages hit the last entry of the stack.
        """
        self.history_stack.append(home_state)
        # print('Homestack is now', self.history_stack, home_state)
        self.home_state = home_state

    def stack_replace(self, home_state):
        self.history_stack[-1] = home_state
        # print('Homestack is now', self.history_stack, home_state)
        self.home_state = home_state

    def stack_release(self, home_state):
        """Safely remove the given name from the end of the stack.
        """
        if self.history_stack[-1] != home_state:
            raise Exception(f'Cannot unstack {home_state}, without a match', self.history_stack)

        r = self.history_stack.pop()
        self.home_state = self.history_stack[-1]
        return r

    def all_clients(self):
        return self.get_manager().get_clients()

    def assign_envelope(self, envelope_plugin):
        """Called early by the state machine when the socket initially arrives
        Apply the given envelope_plugin as the `self.envelope`, allowing the
        envelope to wrap the send() and receive() methods.
        """
        # print('Doping Socket', self)
        self.envelope = envelope_plugin

    def first_mount(self, manager, init_home_state=None):

        # print(f'{self}.first_mount in state:', init_home_state)
        current_state = init_home_state or self.home_state
        self.home_state = current_state
        self.history_stack = [current_state]
        self._manager = manager

        return True

    def get_manager(self):
        '''Return the connection.manager
        '''
        return self._manager



    # async def send(self, message: Message) -> None:
    #     """
    #     Send ASGI websocket messages, ensuring valid state transitions.
    #     """
    #     if self.application_state == WebSocketState.CONNECTING:
    #         message_type = message["type"]
    #         assert message_type in {"websocket.accept", "websocket.close"}
    #         if message_type == "websocket.close":
    #             self.application_state = WebSocketState.DISCONNECTED
    #         else:
    #             self.application_state = WebSocketState.CONNECTED
    #         await self._send(message)
    #     elif self.application_state == WebSocketState.CONNECTED:
    #         message_type = message["type"]
    #         assert message_type in {"websocket.send", "websocket.close"}
    #         if message_type == "websocket.close":
    #             self.application_state = WebSocketState.DISCONNECTED
    #         await self._send(message)
    #     else:
    #         raise RuntimeError('Cannot call "send" once a close message has been sent.')



WebSocket = PortWebSocket
