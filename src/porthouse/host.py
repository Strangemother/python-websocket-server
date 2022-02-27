import sys
from pathlib import Path
from typing import List


from .ingress import app
from .ingress.base import mount_jinja_home
from .house import connection
from . import envelope, lockspace, pipes
from .client import WebSocket


envelopes = ( envelope.MessageCast(), )
live = (
        pipes.PipesSpace(),
    )


state_machine = lockspace.Machine(envelopes, live)
con_manager = connection.Manager(state_machine)

globals()['app'] = app


@app.on_event("startup")
async def startup_event():
    """Run the host manager within the async for await tools"""
    await con_manager.mount()


mount_jinja_home(app, 'index_with_headers.html')


@app.websocket("/")
async def websocket_endpoint_master(websocket: WebSocket):
    # print('Websocket on master port')
    await con_manager.master_ingress(websocket)


@app.websocket("/service/{uuid}")
async def websocket_endpoint_master(websocket: WebSocket, uuid):
    # print('Websocket on master port')
    await con_manager.service_ingress(websocket, service_uuid=uuid)
