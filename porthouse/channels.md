# Sockets and Identities (Channels.)

A Socket connects with a Unique ID (SOCK_ID)
A Client has a unique id (CID)

A socket may authenticate as many clients; e.g. SOCK_ID #1001 is BEN and AMY.
A client may have may open sockets, e.g AMY has open SOCK_ID #1001 and #1002

An ingresss message is received through a socket id channel, sent to the subscribed to _target_ of the message.
This is profiled by the CID connection. Where a CID must be a valid user, and the valid user has 1+ sockets open.


Thus a message from SOCK#1001 is from AMY, but not from SOCK#1002.
The client may view all clients under their ID; seeing incoming socket ids and monitoring their allowances.


A socket ID connects to a channel
a channel ID connects to a socket

When a message is sent to the server, its received through the socket pipe, into the "client message pipe" onto the destination.
The destination is another socket id (direct messaging), to another _channel_ (A room or client pipe).


A lockspace may also have an open channel, named by the lockspace identity.

    Socket connects:
        UUID 12, Client ID "egg" -> send message (no dest) -> UUID -> Egg.subscribers


# Transport Pipes

A messaging layer must bridge SOCK IDS to other CID, rooms, channels etc.
This should be done through its own layer - dubbed transport pipes.

A Message enters the _pipe_ to be pushes through a series of gates until the destination is applied.
Each _Step_ will likely bridge through another channel, and may need to _reauthenticate_ or have additional requirements before the content is moved.


The transport pipes connect socket to sockets - through client configs. The inner components are invisible outside the network.


    Message in: UUID
        UUID -> CID
                    -> service channels
                    -> 'cooked' pipes
                    -> destination
                        -> CID
                            -> UUID_X
                            -> UUID_Y
                                -> CID
                                    ...

Each step likely has a 'send' process for service announcements.

---

In the first version, A socket is associated to a user, A message _emits_ upon the client_ID channel.
The message is send to all users within the same room. If the target exists The message routes the the listed destinations.

Pipes have less functionality than a room - keeping the key features to _bridging_ IO. Any validation may occur on the _entry_ of the step to a new channel; or through a _knuckle_ of the graph during transit.

A `Message` is dropped into the pipes machine and essentially forgotten, the pipes manage the tranmission and persistence of the message instance.
