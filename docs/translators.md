# Envelopes


The side-loaded 'translators' - or known as "envelopes" wrap every message through a list of _inbound_ and _outbound_ message wrappers. Allowing the inspection of a package as it enters and leaves the network.

This is useful for transport language communication, or concorrent testing of a socket. At any point this translator may communicate to, or close the socket before the information reaches the destination.

```py
class UnwrapLang(Envelope):

    def inbound(self, message:[str, bytes], socket:Websocket):
        return json.loads(message)

    def outbound(self, data:[dict, str], socket):
        return json.dump(data)
```

This module _always_ runs on every message for a socket. As opposed to the state-machine plugin where it potentially _locks_ the sequence of messages until unyielding.

