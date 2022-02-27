

version 2.0 is clearer to segregate user entry; through steps govenerned by a 'room'.

The room will have configurable 'blocks' as a header config. Entering users complete usual auth.


1. A user connects
2. Auth is checked, moved to lobby or room
3. In the lobby perform an auth sequence (based on user)
4. connect to room and perform room dance
5. emit/receive messages

---

The entire process will be as transparent as possible the user auth should consist of:

+ An account, with new connection keys
+ A specific url
+ A 'handshake' header cookie
+ auth dance 1
+ room dance

---

The user flow should be:

1. Create an account `foo` - generates a `user-gen-uuid`
2. make a room `room`
3. connect to the room `ws://smum.uk/user-gen-uuid/room`
4. perform dance
5. emit messages

or

3. connect to lobby: `ws://smum.uk/user/foo/`
4. perform admin dance
5. send command `connect to room`
6. backend moves user into room
7. perform dance
8. emit messages

Auto flows would be preferable, configuring through the UI

3. device connect to `ws//../user-gen-uuid/room/client-uuid/`
4. send pre-defined challenge
5. device responds
6. backend moves device into room

---

Mandated rooms:

1. The 'technical channel' for all users
2. The 'lobby' for incoming users
3. A user lobby
4. the room

All users bind to a technical channel, emitting public wide events (disconnects etc).
The main lobby for all incoming users, and dispatch to rooms after auth

The user lobby accepts any user incoming connection, and used as a personal 'dev' and 'testing' room.

The actual room defines the group of users and devices in one conversation. This defines the features the admin requires for a feature-set.

---

A user has one lobby for all incoming streams and many rooms. Each room is designated for task, allowances, or general user tooling. The messages within are structures, defined as per the room config.

some rooms are dedicated to IoT devices, and config is done _in the room admin interface_, broadcasting bytes to all ssh-key authed devices.

In 'chat rooms' board of historical text messages form the base, with user interaction and oauth based access.


---

Channels within a room help break-up quantified data into subsets:

    ws//smum.uk/user-gen-uuid/room/client-uuid/channel
    ws://smum.uk/user-gen-uuid/room/channel

All channels within the room act the same and count towards the overall stats for a single room. This is useful for data presentation or many discrete devices connecting to a 'ready' room.

For example a UI table of many cells may present the all channels of one room. Each cell would subscribe to a single channel.

A connection may subscribe to many channels within a room, but would need to reauthenticate if the connection requests entry to a room.

---

Multi-casting to the central unit - or _aggregating_ many connections through one bus should incorporate a new _instance_ of the socket server, with a binding to emit messages into the destination.

For example many devices within one building may aggregate to an on site instance, of which emits all the information into one remote room. The remote room will recieve the same data-packets as the remote, albeit with a delay.



---

If a user connects through the frontend socket, they're greeted witha strict chat bot. If refused the chatbot will drop connection

    > connect
    >> sending command tty mode
    > command: ttymode
    # ! (user view should pretence teleprompt return carraige)
    > hello ...
    > welcome .... please perform >
    .> ...
    > !! incorrect
    .drop.

on repeat

    > ooh you again! ... Nope!.
    .drop.

---

The user can move to their admin lobby


---

A socket has a state, which is _doped_ upon accept through the plugins.

The socket should be pushed into states as it progesses until it moves to a designated room or channel.

for any socket assign an id and check its current state. Each position in the state machine is an acceptor function, and the socket must send the right values to the acceptor for it to proceed to the next step.

The websocket connects, providing a state of 0. It must perform the actions designated by that state. IT's bi-directional - as such the plugin may _talk_ to the socket.

The plugin can see the current state of the plugin `get_state(websocket)` which is unique to this socket. If the socket is pre-authenticated the state for this plugin will be _finished_.


---

## Session history room

If a connection to a room has 'session history', every message emit from this connection is replayed from the start to any new connection to the room.

IF the owning connection is dropped, the messages are wiped and replay doesn't occur.
Any existing connection in the room will not receive the replay events, as they already received them. Messages after the replay continue to all nodes as normal.

For example a 'rendering' connection opens to serve A - Z actions. The listener recieves all. A new connection attends to recieve A-Z _after_ the messages are played. Node A and B are up-to-date.


---

A client id is `id(websocket)`, but is attached to a channel ID of the UUID client id
All clients gain a UUID once processed; attached to the unique socket.
Many sockets may use the same ID - known as "cloning"

When a client send a message, its dispatched through the channels graph _from_ the UUID to the target. The graph machinery pushes the message to all _listeners_. If there are not listeners for a message (allocated by target uuid) the message dies in the void.

