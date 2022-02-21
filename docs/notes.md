
Every socket has a unique UUID assigned on entry. This doesn't change but is not
the _client_ or _user_.

An entry module assigns the ID  of which becomes a soft channel. In turn a service UUID may exist, monitoring the events and flow of the uuid.

Usually a service wocket for a unique uuid isn't require but will allow the event and flow ch changes from an external socket, not governed by the socket datatype.

---

# Channels

A channel is a the primary event bus, pushed into a graph, moving the message to the correct microstate.

This makes it easy to quickly dispatch to mutlple channels or active a channel if new.


# Listeners

For every UUID (websocket) is assigned to a true _client_ and its allowed internals. The client may send and recieve messages to target clients. a client may nominate to _listen_ to a uuid - such as a peering chat or service channel.


---


The 'entry flow' should allow a user to allocate their identity to a socket, given the header sequences within the state machine. Once resolved (All required params are met), the socket is designated an internal identity, allowing the entry to a room. The room manages all concurrent messages and any channels within.

1. Access the network
2. Discover Identity
3. Move to a room


As the new connection is allocated a persistent ID; we can monitor this one 'user channel' for all incoming connections.
