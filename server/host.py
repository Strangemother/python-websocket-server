from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from . import manager
import sys
from pathlib import Path


PORT = 8007

app = FastAPI()
host = manager.Host()


@app.on_event("startup")
async def startup_event():
    global register
    await host.mount()


@app.on_event("shutdown")
def shutdown_event():
    register.close()
    # with open("log.txt", mode="a") as log:
    #     log.write("Application shutdown\n")

from . import home


@app.get("/")
async def get():
    return HTMLResponse(home.html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await host.connect(websocket)

    allow_continue = 1

    try:
        while allow_continue:
            data = await websocket.receive_text()
            allow_continue = await host.receive_text(data, websocket)
    except WebSocketDisconnect:
        host.disconnect(websocket)
        await host.broadcast(f"Client #{client_id} left the chat")
