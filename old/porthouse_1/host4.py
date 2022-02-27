import sys
from pathlib import Path
from typing import List


from .ingress import app
from .ingress.base import mount_jinja_home
from .house import connection
from . import envelope, spaces, v2

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse


# Internal Channels, mapping IDS to profiles, and other channels.
CHANNELS = {
    'egg': { 'name': 'Dave' },
    'poppy': { 'name': 'Eric' },
}

from . import tspace

envelopes = ( envelope.MessageCast(), )
live = (
            # spaces.Limbo(),
            # spaces.Sibling(),
            # spaces.Other(),
            # spaces.IdentifierLockSpace(channels=CHANNELS, next_place='broadcast'),
            # spaces.BroadcastLockSpace(channels=CHANNELS),
        tspace.PipesSpace(),
            # spaces.ChannelDeliveryLockSpace(channels=CHANNELS),
    )


state_machine = v2.Machine2(envelopes, live)
con_manager = connection.Manager(state_machine)

globals()['app'] = app


@app.on_event("startup")
async def startup_event():
    """Run the host manager within the async for await tools"""
    await con_manager.mount()


mount_jinja_home(app)


@app.websocket("/")
async def websocket_endpoint_master(websocket: WebSocket):
    # print('Websocket on master port')
    await con_manager.master_ingress(websocket)


@app.websocket("/service/{uuid}")
async def websocket_endpoint_master(websocket: WebSocket, uuid):
    # print('Websocket on master port')
    await con_manager.service_ingress(websocket, service_uuid=uuid)
