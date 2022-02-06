import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .ingress import app
from .house import connection
from . import home


con_manager = connection.Manager(app)

# import scene

# PORT = 8000
# DEVICES = (
#         scene.SceneManager,
#         manager.BroadcastDevice,
#     )

# host = manager.Host(devices=DEVICES)

@app.on_event("startup")
async def startup_event():
    """Run the host manager within the async for await tools"""
    await con_manager.mount()


globals()['app'] = app

# from ingress import *

@app.get("/")
async def get():
    return HTMLResponse(home.html)


@app.websocket("/")
async def websocket_endpoint_master(websocket: WebSocket):
    print('Websocket on master port')
    await con_manager.master_ingress(websocket)


@app.websocket("/{user_uuid}/")
async def websocket_endpoint_user(websocket: WebSocket, user_uuid: str):
    print('Websocket on user port for', user_uuid)
    await con_manager.uuid_ingress(websocket, user_uuid)
