"""The 'Singleton' defines the initial exeuction of the FastAPI _app_ and the
head within.

At this point monkey-patch the starlette Websocket class within the runtime
to ensure the entire service utilises the one client class.

"""
import sys
from pydoc import locate

#from . import client
from porthouse import client, conf

"""Gather the websocket class from the config or use PortWebSocket
"""
# WebSocketClass = locate(conf.WEBSOCKET_CLASS) or client.PortWebSocket
WebSocketClass = conf.resolve('WEBSOCKET_CLASS', client.PortWebSocket)

# monkey-patch
sys.modules.get('starlette.websockets').WebSocket = WebSocketClass

"""The FastAPI import must occur _after_ the starlette monkey-punch to ensure
the imports within fastpi are _fresh_.
"""
from fastapi import FastAPI

app = FastAPI(host=conf.HOST, debug=conf.DEBUG)
# host = manager.Host(devices=DEVICES)
