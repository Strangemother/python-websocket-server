import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from ingress import app, host
import manager, home
import scene

# PORT = 8000
# DEVICES = (
#         scene.SceneManager,
#         manager.BroadcastDevice,
#     )

# host = manager.Host(devices=DEVICES)

globals()['app'] = app

from ingress import *

@app.get("/")
async def get():
    return HTMLResponse(home.html)

