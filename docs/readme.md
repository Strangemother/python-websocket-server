# Porthouse

Porthouse is a websocket server library, with internal utilities to build a custom socket platform.
Built upon FastAPI and Starlette.


## Getting Started


```py

# Message Wrappers
envelopes = ( envelope.MessageCast(), )

# Pocket spaces.
lockspaces = (
    spaces.IdentifierLockSpace(),
    spaces.ChannelDeliveryLockSpace(),
)

# Executor
machine = v2.Machine2(envelopes, lockspaces)

# acceptor
manager = connection.Manager(machine)

# Mount and bind
await manager.mount()
await manager.master_ingress(websocket)
```


## Parts

The Porthouse library is designed to manage async sockets with the ease of standard connections. Offset large tasks to lock-spaces, or test every step with envelopes


## Envelopes

An `Envelope` wraps inbound and outbound discrete messages from a socket. Many envelopes may execute upon a message, ran procedually in the original order given.

A useful freebie `envelope.MessageCast()` converts an inbound message to a `Message` type, allowing for easier conversion of text/json to a python classy object.

> Consider Envelopes like _middleware_ intecepting every message between the client and server.

## LockSpaces

A `LockSpace` aims to simplify a group of messages until the _space_ yields ownership of the socket. A client is forced to communicate to one lockspace until _released_. This continues forever.

> Lockspaces are similar to "rooms". Moving to other _rooms_ is done serverside.

The `spaces.Limbo()` lockspace is a good example of how to move a client another lockspace

```py
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

```

If the user sends a message matching the name of another lockspace, the client socket is released.
Note this isn't safe for a production environment.


### Connection Manager

Accept incoming sockets and farm sockets to the Machine.

1. Accept incoming connections
2. Push any messages
3. Announce disconnects

The connection manager maintains a list of all clients and keeps then within a pong loop.
All _work_ is done within the main machine.


### Entry Machine

The _Entry Machine_ manages the entire process for incoming socket.

1. accept _commands_ from the connection manager
2. move a socket through lockspaces
3. Announce changes through connected lockspaces


Funtionally the Machine acts as a huge plugin suite, calling the correct `Lockspace` placements for incoming messages.
