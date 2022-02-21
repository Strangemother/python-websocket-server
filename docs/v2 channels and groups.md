

In version 2 the internal servicing should change, allowing a single PortSocket
to connect and be pushed through named areas. In each point the content
poisions the owning socket

The socket identity lives in the persistent head.
A socket joining must gather an ID, then emit messages

The allowance of the ID provides packet direction within the network, the destination unwrapped from the content (if nominated.)

When a socket moves to an area, its channel content are piped to the associated 'group' id - a receiving machine or the target identifier

1. A socket enters
    + Given a socket id
    + socket tests identity
2. Identity lobby
    A user is stuck in 'limbo' until they resolve an ID. The tests within the limbo room govern drops.
3. socket Channel (Id'd pipe)
    The socket is identified and given a persistent channel to comminicate upon
    Any incoming messages post to the 'socket channel', into the 'identified channel' onto the destinations
4. Grouping and messages
    A Socket dispatches messages to a target. If no target the group configuration takes precedence.

An envelope tests for the identity. If the envelope fails, it moves the socket to the owning room.

As such the socket moves into assigned _lobbys_ until they're released.

    socket enter -> Get ID -> Validate ID -> move to specified -> wait.


## Rooms

A 'room' is a configuration with a UUID. The user may post messages to the _room_, and subscribers to the room are called.
Connections look like:

    Socket id -> identity ID -> room id

Each 'group' is bound to the last through a graph. A waking client is applied the new message group IDs, appending new IDS to _recievers_ through progression.

    socket enters UUID -> id == 33

        channel(id=33).add(UUID)

    socket enters UUID_2 -> id == 33

        channel(id=33).add(UUID_2)

Then room assocation previously assigned.

    room(12).add(id=33)
    client(33).rooms()
    => 12, 44, 101

When the client sends a message, it can reache rooms 12, 44, 101

    client send { to: room:101, text:apples }

    (socket) UUID -> client(33) -> room(101) -> "apples"



## Lock Space


A Lock Space identifies a _lobby_ for where the socket much compete a task before moving to the next location.
The space may be nominated or forced, keeping an index key within the PortSocket.

Locking should be depth framed. A parent may call upon a _lock_, until it returns the final value. The _lock_ may ask for an additional LockSpace, and instead wait upon that. The resolution of the locking should destack until the original parent resolves.

This should occcur within the same _frame_, so a client may unwind a nested lock space within one wait cycle.

    Client send "Room:12" -> lock _identity room_ -> Move into "ask id lock" -> step into "wait SSH key" lock.

    ... and then unwind.

    ssh key (key) -> id lock (confirmed) -> Identity room (client name) ... >> move to room "client name:12".

---

To do this, the initial request is applied to _entry_ lockspace. This Limbo Lobby dutifly moves the client into the correct next wait room.

the wind stack should assign a key, value for each position.

    >>> socket.stack
    ['lobby', 'id_room', 'channel_service']
    # move to staock
    >>> socket.move_to(room(23))

room(23) required an ID, and will move the client into the locking room until resolved:

```py
class Room(object):

    def initial(self, socket):

        if not socket.has_id():
            ok = await socket.move_to(room('id_room'))
            if not ok:
                return socket.drop()

        if self.has_access(socket.client_id):
            self.subscribe(socket.client_id)
```

The room will communicate to all subscribers (defined by the room spec), given messages from a client

    >>> socket.send('Hello All')


```py
class Room(object):

    def message(self, data, socket):
        for soc in self.get_client_sockets():
            if soc is socket:
                continue
            await soc.send(data)

```

data mapping considerations:

    socket_id:
        to: client_id
            client_id_2

    client_id:
        rooms: room(33)
               room(12)
               room(101)
        to: service_client_id_2

    room(33):
        clients:
            client_id_2
            client_id_X

        groups:
            debug_service_1
            cluster_host_03


As such, when a socket wants to send a message to a room - it's the socket UUID connecting to the client channel, connecting to its rooms.




