from pydoc import locate
import sys


HOST = '127.0.0.1'
WEBSOCKET_CLASS = 'porthouse.client.PortWebSocket'
MESSAGE_CLASS = 'porthouse.envelope.CustomMessage'
DEBUG = True

UNDEFINED = {}


SELF = sys.modules[__name__]


def resolve(name, default=UNDEFINED):
    # WebSocketClass =
    attr = getattr(SELF, name, default)

    res = (locate(attr) or default) if attr is not default else default

    if res is default:
        print(f'{__spec__.name} return default for {name}')

    if res is UNDEFINED:
        raise KeyError(f'{__spec__.name} cannot resolve {name}')

    return res
