# House Connection Manager


The input manager handles ingress and drops of all docket connections, farmed from the host wsgi function into `master_ingress(websocket)`.

A prepared socket is pushed into a async wait loop until a disconnect occurs.

To use the manager, create a new instance and call the master_ingress or `uuid_ingress` function to initiate a flow on the socket:


```py
con_manager = connection.Manager(state_machine)
await con_manager.mount()
await con_manager.master_ingress(websocket)
```

The host calling these functions doesn't care about the rest - of which is handled within this manager or the referenced `state_machine`.


# How does it work

Fundamentally the builtin `Manager` handles _ingress_, the receive loop and _disconnect_. All other actions are farmed to the given `state_machine`.

The functions called upon the state machine handle every processed action:

```py
state_machine.initial_entry(websocket)
keep_open = state_machine.push_message(data, websocket)
state_machine.disconnecting_socket(websocket, client_id, error)
```

Internally the manager ensures the docket is _accepted_ and waits for any incoming content.
If the `push_message` method returns `keep_open=False`, the socket is closed immediately using the `manager.disconnect_socket` => `state_machine.disconnect_socket` announcement.

In all cases the the manager cares for _an open connection_ - the state manager handles data trafficking.
