"""The states provide the _current state_ of a websocket. Essentially each
socket has a unique data-area for each plugin, allowing the unique flow of a
socket through shared paths.
"""


class PairStateMixin(object):
    def set_pair_state(self, acceptor_pos, internal_pos, websocket):
        _id = id(websocket)
        st = self._states[_id] = (acceptor_pos, internal_pos,)

    def get_pair_state(self, websocket) -> tuple:
        """Get the internal pair state
        """
        _id = id(websocket)
        st = self._states.get(_id, (0, None,))
        return st

    def set_internal_position(self, internal_pos, websocket):
        """
        self.set_internal_position(internal_pos, websocket)
        """
        _id = id(websocket)
        try:
            st = self._states[_id]
        except KeyError:
            st = (0, None,)

        nv = (st[0], internal_pos)
        self._states[_id] = nv
        # st = self._states[_id] = (acceptor_pos, internal_pos,)
        return nv


class Lobby(PairStateMixin):
    """Anyone within the lobby must resolve an ID to to move into
    a 'room' - performing their states.
    """
    name = 'lobby'
    state_index = None

    def __init__(self, name=None, state_index=None, acceptors=None):
        self._states = {}
        self.name = name or self.name
        if state_index is not None:
            self.state_index =  state_index
        # A list of live classes with internal steppers.
        self.acceptors = acceptors or ()

    def pop_state(self):
        return (self.state_index, self.name,)

    def mount(self, state_machine, index, parent=None):
        # self._states = state_machine._states
        if self.state_index is None:
            print(self, 'state index', index)
            self.state_index = index

        for i, pl in enumerate(self.acceptors):
            pl.mount(state_machine, i, self)

    async def inbound(self, websocket, last_data=None):
        """messages are likely to appear from this socket.
        """
        acceptor_position, micro_position = self.get_pair_state(websocket)
        try:
            acceptor = self.acceptors[acceptor_position]
        except IndexError as e:
            # no acceptor functions.
            return self.no_acceptors(None, micro_pos, acceptor_pos, websocket, last_data)
        return await acceptor.inbound(websocket, last_data=last_data)

    async def tell_service(self, **kw):
        pass #print('Tell', kw)

    async def push_message(self, data, websocket):
        """A message inbound at this current position.
        If the user has presented the correct message, approve - else deny.

        Must return a 'keep alive' bool, else the socket is dropped.
        """

        # get id state
        # push through function
        # approve, deny, move

        print(f'{self.name}.push_message. State:', data, websocket)
        await self.tell_service(
                owner=websocket,
                data=data,
                action='push_message',
                )
        # Get the current (micro) state; run through the functions until each resolve.
        acceptor_position, micro_position = self.get_pair_state(websocket)

        try:
            current_plugin = self.acceptors[acceptor_position]
            push_func = current_plugin.push_state_message
        except IndexError:
            # There are no more acceptors at the given position.
            # The socket should be reseated or dropped
            print('Finished all acceptors for', self)
            push_func = self.dead_letter# (data, websocket, acceptor_position, micro_position)

        move_bool, internal_pos = await push_func(micro_position, data, websocket)

        acceptor_pos = acceptor_position + int(move_bool)
        internal_pos = (micro_position or 0) + int(internal_pos)

        self.set_pair_state(acceptor_pos, internal_pos, websocket)

        keep_open = 1

        if move_bool:
            keep_open = await self.step_acceptors(websocket, data, current_plugin, acceptor_pos, internal_pos)
        return keep_open

    async def step_acceptors(self, websocket, data, current_plugin, acceptor_pos, internal_pos):
        """
        Step from one acceptor to the next after the acceptor_pos has been moved
        due to the previous plugin. Return a 'keep open' bool.

            keep_open = await self.step_acceptors(
                                websocket, data, acceptor_pos, internal_pos)

        The current_plugin was the actioned item to perform the last step request
        The next plugin _accept_pos_ may not exist.

        If a next plugin is not found call `no_acceptors` and return a keep alive
        bool.
        """

        # current_plugin = self.acceptors[acceptor_pos]
        # The microstate has asked for a release., Announce the closure
        # and inbound of the websocket.
        keep_open = await current_plugin.outbound(websocket, data)
        try:
            acceptor = self.acceptors[acceptor_pos]
            keep_open, internal_pos = await acceptor.inbound(websocket, last_data=data)
            self.set_internal_position(internal_pos, websocket)
        except IndexError:
            # No more future acceptors.
            keep_open = await self.no_acceptors(current_plugin, internal_pos, acceptor_pos, websocket, data)

        return keep_open

    async def no_acceptors(self, plugin, internal_pos, acceptor_pos, websocket, data):
        """The last move has pushed this socket to the end of all acceptors.
        As such the next call will resolve to the dead-letter.
        """
        print('End of the line for', websocket)
        # keep_open = 1
        # return 1
        await self.tell_service(
                owner=websocket,
                plugin=plugin,
                internal_pos=internal_pos,
                acceptor_pos=acceptor_pos,
                action='no_acceptors',
                data=data,
                )
        raise Done(1, plugin, acceptor_pos, internal_pos, self)

    async def dead_letter(self, micro_position, data, websocket):
        """The data from the given websocket has no place as all acceptors
        are done.
        """
        print('dead_letter', micro_position, data, websocket)
        await self.tell_service(
                owner=websocket,
                action='dead_letter',
                data=data,
                )
        return False, 0# micro_position


class VoidNoState(Lobby):
    """A Mailroom for void messages
    """
    name = 'void_room'
    state_index = -2


class MicroState(PairStateMixin):
    """A micro state lives within a Lobby to digest incoming functions as a
    group receiving "inbound", _messages_ and "outbound" upon a single websocket
    per transation,

    """

    _index = None
    name = 'microstate'
    def __init__(self, name=None):
        self.name = name or self.name
        self._states = {}

    def mount(self, state_machine, index=-1, parent=None):
        self._index = index

    def pop_state(self):
        return (self._index, self.name,)

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.name}#{self._index}>'

    async def inbound(self, owner, last_data=None):
        """Called before the microstate is active, after the last state is released
        before any _entry_ messages.

        Return the 'keep open' state of the socket. If false or 0 is returned the
        socket will close 1000
        """
        print('Okay,', self.name, ' expecting', owner, 'soon')
        # keep open, new micro_position.
        return 1, None

    async def push_message(self, data, owner):
        """Called by the Manager if this microstate was applied to the
        plugin list and the response content is _not_ sent to the Lobby push state.

            plugins = (
                state.MicroState(name='BEFORE'),
                # ...
            )

            state_machine = state.StateMachine(plugins,)

            await state_machine.push_message(data, websocket)
            # Calls this in proc

        """
        keep_open = 1
        a, m = self.get_pair_state(owner)
        # a_pos, micro_pos = self.parent.get_pair_state(owner)
        move_on, micro_step = await self.push_state_message(m, data, owner)
        m = 0 if m is None else m
        nv = m + int(micro_step)
        self.set_internal_position(nv, owner)
        release = nv > 5
        print(self.name, f'send: micro_step={micro_step}. Release:', release)
        if release:
            self.release()
        # self.release()

        return keep_open

    def release(self):
        #keep_alive, macro, acceptor_pos, internal_pos, _plug = err.args
        raise Done(1, self, self._index, 0, self)


    async def push_state_message(self, micro_position, data, owner):
        """A message from the lobby 'push message'. Given this is a sub state
        the micro position should manage the internal stepper.

            ms = acceptors[acceptor_position].push_state_message(micro_position, data, owner)
        """
        # The input is new if the microstate doesn't exist.
        func = self.entry if micro_position is None else self.concurrent
        # move_on, micro_step = await func(data, owner, micro_position)
        return await func(data, owner, micro_position)


    async def entry(self, data, owner, micro_position):
        # New socket into this micro state
        #
        # Move forward; current internal state
        print('New Unit in state', owner, data)
        # return False, 0

        # In this example, rather than send (False, continue=0), we send
        # True, providing the _concurrent_ method a microposition of +1
        return False, True

    async def concurrent(self, data, owner, micro_position):
        # an existing socket feeding data to this unit
        move_on = micro_position >= 2
        print(f'Concurrent {self} at micro_position={micro_position} move_on={move_on}', data)
        # after _moveon_ this microstate no-longer binds the socket messages
        # and _releases_ the flow.
        return move_on, True

    async def outbound(self, owner, last_data=None):
        """This socket has been moved from this plugin, and the next plugin
        will receive an inbound request.
        """
        print('Socket outbound', self.name, owner)
        # keep open
        return 1


# PLUGINS = (
#     VoidNoState(),
#     Lobby(name='lobby',
#           state_index=-1,
#           acceptors=(
#                 # User identifier
#                 # Room identifier
#               MicroState(),
#               MicroState(),
#             )
#          ),
# )


class StateMachine(object):
    """The State Machine holds all information about the sockets. Using
    a single `get_state(websocket)` on a plugin returns current state for
    the plugin and live socket.

    Each state position is a function to validate the current role and
    _move_ the socket into the next state when released.
    """

    def __init__(self, user_plugins=None, entry_acceptors=None):
        print('New State Machine')
        # Key to int mapping.
        self._states = {}
        # Int to name mapping
        self.state_map = {}
        # name to instance mapping
        self.plugins = {}
        self.entry_acceptors = entry_acceptors or ()
        self.mount_plugins(user_plugins)

    def get_core_plugins(self):
        return (
            VoidNoState(),
            Lobby(name='lobby',
                state_index=-1,
                # User identifier
                # Room identifier
                acceptors=self.entry_acceptors,
            )
        )

    def mount_plugins(self, user_plugins=None):
        plugins = self.get_core_plugins()
        up = tuple(user_plugins or ())
        lp = len(plugins)

        for i, pl in enumerate(plugins + up):
            # pl = Pl()
            self.mount_plugin(pl, i-lp)


    def mount_plugin(self, pl, index):
        ps = pl.pop_state()
        i = index if ps[0] is None else ps[0]
        self.state_map[i] = ps[1]
        pl.mount(self, i)
        print('mount', pl, i)
        self.plugins[ps[1]] = pl

    async def initial_entry(self, websocket):
        """The new websocket is requesting access and has been accepted onto
        the network.
        As this is a 'first wake', the next input will be a 'receive'.
        we inform the 'inbound' of the mounted plugins for the first plugin.
        """
        pl = self.get_current_state_plugin(websocket)
        return await pl.inbound(websocket)

    async def push_message(self, data, websocket):
        """ Given a message send to the correct digest function.

                await state_machine.push_message(data, websocket)

            return keep-alive boolean
        """
        plugin = self.get_current_state_plugin(websocket)
        # run and retrn a bool.
        try:
            return await plugin.push_message(data, websocket)
        except Done as err:
            # should we move or stay
            # raise Done(1, plugin, acceptor_pos, internal_pos, self)
            keep_alive, macro, acceptor_pos, internal_pos, _plug = err.args
            slid = self.slide_state_int(websocket, int(keep_alive))

            print(f'\nPlugin {plugin} raised Done - from: {macro}. Slid:', slid)

            return keep_alive

    def get_current_state_plugin(self, websocket):
        # find cuurrent state
        ws_state = self.get_state_int(websocket)
        # resolve to function
        pl = self.get_mapped_plugin(ws_state)

        if pl is None:
            print(f'\nThe requested plugin: {ws_state}, does not exist.')
            # print(state_map)
            print('Available:', tuple(self.plugins.keys()))
            # pl = self.plugins.get(state_map.get(-2)) #void
            pl = self.get_mapped_plugin(-2) # void
        return pl

    def get_mapped_plugin(self, int_id):
        # resolve to function
        state_map = {
            -2: 'void_room',
            0: 'run_states',
            **self.state_map
        }

        return self.plugins.get(state_map.get(int_id)) #void

    async def lobby(self, data, websocket):
        """The user is in -1 state and this inbound data should start
        upon the lobby validation.

        return a continue bool.
        """
        _id = id(websocket)
        print('User presented info to the lobby', _id, data)

        # now we run the sequence of steps to resolve the user into the next
        # state. For each step a function recieves the data. Given the transation
        # method this will approve or reject the message.
        # The state is moved by the plugin when required.

        return 1

    def slide_state_int(self, websocket, add_value=1):
        _id = id(websocket)
        new_state_int = self.get_state_int(websocket) + add_value
        # v = self._states[_id]
        self._states[_id] = new_state_int
        # self._states[_id] = (new_state_int,) + v[1:]

        return new_state_int

    def get_state_int(self, websocket):

        # get the id,
        # pull the state from the OD resolved dict.
        _id = id(websocket)
        current_state = self._states.get(_id)
        if current_state is None:
            return self.no_state(websocket)
        return current_state

    def no_state(self, websocket):
        # Apply a new start state for the given socket
        _id = id(websocket)
        v = -1
        # self._states[_id] = v
        print(f'No State {_id} == {v}')
        return v


class Done(Exception):
    pass
