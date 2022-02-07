# Micro States

The built-in "State Machine" ensures a procedural sequence for an incoming socket, decoupled from the connections and general life of a socket.

A single micro state, implements a fixed flow until a _release_ into another flow through many micro states. A single Lobby may manage many micro states, all ran through the state machine.


# Usage

The host and its ingress receivers call upon a `connection.Manager` of which accepts a freshly made state machine.

First we'll need a base setup:

1. Create a state machine
2. Given it to a new manager
3. Execute on incoming connections

```py
from porthouse.house import connection
from porthouse import state

plugins = (
        # ... MicroStates here.
    )

state_machine = state.StateMachine(plugins)

# Boilerplate ...
#
con_manager = connection.Manager(state_machine)

# FastAPI integration.
#
@app.on_event("startup")
async def startup_event():
    """Run the host manager within the async for await tools"""
    await con_manager.mount()


@app.websocket("/")
async def websocket_endpoint_master(websocket: WebSocket):
    print('Websocket on master port')
    await con_manager.master_ingress(websocket)
```

When a new connection occurs on the root path, e.g: `ws://localhost:8000/`, the connection is passed to the connection manager `master_ingress`

---

For other examples we can assume this `host` setup.

## Adding Acceptors

Within the framework we generally call a state-machine plugin an "acceptor" - as they accept and transition a socket through distinct stages, accepting (or dropping) the connection when required.

Without a plugin set (Acceptors) the state machine will do nothing, and simply dump all incoming messages to the `dead_letter` function:

```py
state_machine = state.StateMachine()
con_manager = connection.Manager(state_machine)
```

With an incoming message, the state machine received the `Done` command early, thus all incoming messages are sent to dead letter:

```py
>>> keep_open = state_machine.push_message(data, websocket)

!The state machine resolved Done at entry...

lobby.push_message. State: {'type': 'websocket.receive', 'bytes': b'\x00'}
Finished all acceptors for <porthouse.state.Lobby object at 0x000000000402D1D0>
dead_letter None {'type': 'websocket.receive', 'bytes': b'\x00'}

>>> keep_open = state_machine.push_message(data, websocket)

lobby.push_message. State: {'type': 'websocket.receive', 'bytes': b'\x00'}
Finished all acceptors for <porthouse.state.Lobby object at 0x000000000402D1D0>
dead_letter 0 {'type': 'websocket.receive', 'bytes': b'\x00'}
```

### Creating an Acceptor

First we'll build a MicroState acceptor to receive all messages:

```py
class Forever(state.MicroState):
    async def concurrent(self, data, owner, micro_position):
        print('Forever:', data)
        move_on = data.get('text', '').lower() == 'thanks'
        return move_on, True
```

For fun, if the user sends "thanks", the microstate will unlock.


To save keystrokes, use the `entry_acceptors` attribute for easy loadout. You can apply a list of micro states for the connection to step upon each release:

```py
state_machine = state.StateMachine(
        entry_acceptors=(
            Forever(name='FOREVER'),
            # state.MicroState(name='alpha'),
            # state.MicroState(name='beta'),
        )
    )
```

When sending data to the socket, the new microstate immediately accepts the connection:

```py
# ('127.0.0.1', 63454) - "WebSocket /" [accepted]

# Okay, FOREVER  expecting <websocket> soon
>>> data = b"\x00\x00" # 2 null bytes.

>>> keep_open = state_machine.push_message(data, websocket)
lobby.push_message. State: {'type': 'websocket.receive', 'bytes': b'\x00\x00'} <websocket>
<Forever FOREVER#0> receive entry: micro_position= None


>>> keep_open = state_machine.push_message(data, websocket)
lobby.push_message. State: {'type': 'websocket.receive', 'bytes': b'\x00\x00'} <websocket>
Forever: {'type': 'websocket.receive', 'bytes': b'\x00\x00'}

```

In the next message we send the magic "thanks", causing the `Forever` micro state to _release_ into the next state.
As the next plugin (position `0`, any plugins we've applied) doesn't exist, it fails and defaults to the `dead_letter` method:

```py
>>> keep_open = state_machine.push_message("thanks", websocket)
lobby.push_message. State: {'type': 'websocket.receive', 'text': 'thanks'} <websocket>
Forever: {'type': 'websocket.receive', 'text': 'thanks'}
Socket outbound FOREVER <websocket>
End of the line for <websocket>


Plugin <porthouse.state.Lobby object at 0x000000000402E358> raised Done - from: <Forever FOREVER#0>. Slid: 0

# Cannot move on to the 0th acceptor:
The requested plugin: 0, does not exist.
Available: ('void_room', 'lobby')
void_room.push_message. State: {'type': 'websocket.receive', 'bytes': b'\x00\x00'} <websocket>

# As such fallback to the default dead_letter
Finished all acceptors for <porthouse.state.VoidNoState object at 0x000000000402E3C8>
dead_letter None {'type': 'websocket.receive', 'bytes': b'\x00\x00'} <websocket>
```


### Releasing Acceptors

A single Acceptor plugin maintains a lock and release method for a socket. At any point we can choose to _release_ a websocket from this lock, allowing the flow of messages to the next acceptor. This occurs procedurally so we can write a _flow_ of acceptors.

You can release an acceptor through the return value when called, or by executing `release()` of which emits the `Done()` event:

#### Move On flag.

A `push_state_message` returns a tuple of `(move on, internal value)`, where the `move on` is a flag to _release_ this plugin from the bind. The `internal value` is a a position key for this micro state, handled by the state manager.

If the _move on_ is `True` the plugin will release:


```py
class ReleaseOnThanks(state.MicroState):
    async def concurrent(self, data, owner, micro_position):
        move_on = data.get('text', '').lower() == 'thanks'
        return move_on, True
```

Alternatively call upon the `MicroState.release` method:

```py
class ReleaseOnThanks(state.KeyMicroState):
    async def push_state_message(self, micro_position, data, owner):
        t = data.get('text', None)
        if t == 'thanks':
            self.release()

        # move_on, micro_position inc. ignored if 'release' is called.
        return False, True
```

Or raise a `Release`:

```py
class EmitRelease(state.KeyMicroState):
    async def push_state_message(self, micro_position, data, owner):
        if (micro_position or 0) > 2:
            raise state.Release()
        return False, True
```


## Key States:

Generally the Acceptors act as linear procedures the websocket will access in sequence, however we can use the `KeyMicroState` to move to a chosen micro state. For example:

```py
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
            # Debug(),
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
```

In this example upon each message the websocket will flow through this process:

1. Inbound `BEFORE`
2. Move to `beta`
3. move to `other`
4. move to `keyarea`
5. move through the Lobby -> `egg` -> `cake` -> `debug`
6. Upon release from `debug` move to `other`
7. back to #6

Any steps not named in this flow will ignored. In each micro state, the acceptor chooses to _release_ the plugin into the next acceptor.
