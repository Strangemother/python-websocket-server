import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

import manager, home

from scene import device

PORT = 8000
DEVICES = (
        device.SceneManager,
        manager.BroadcastDevice,
    )

app = FastAPI(host='127.0.0.1')
host = manager.Host(devices=DEVICES)


# @app.on_event("startup")
# async def startup_event():
#     await host.mount()


@app.on_event("startup")
async def startup_event():
    await host.mount()

# @app.on_event("shutdown")
# def shutdown_event():
#     register.close()
#     # with open("log.txt", mode="a") as log:
#     #     log.write("Application shutdown\n")


@app.get("/")
async def get():
    return HTMLResponse(home.html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    try:
        print('Accepting Websocket')
        return await host.accept_socket(websocket, client_id)
    except Exception as err:
        print('An error ooccured:', str(err))
        pass


async def accept_socket(websocket, client_id):
    print('Accepting socket')
    # await websocket.accept()
    allow_continue = await host.connect(websocket)

    try:
        while allow_continue:
            if websocket.client_state.value == 1:
                data = await websocket.receive()
                allow_continue = await host.receive(data, websocket)
                if allow_continue == 0:
                    print(f'Signal close receive of {client_id}')
                    await disconnect_socket(websocket, client_id)

    except WebSocketDisconnect as err:
        print('Client disconnect', err)
        await disconnect_socket(websocket, client_id)


async def disconnect_socket(websocket, client_id):
    await host.broadcast(f"Client #{client_id} left the chat", exclude=(websocket,))
    host.disconnect(websocket)
