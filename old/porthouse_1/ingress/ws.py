from fastapi import WebSocket, WebSocketDisconnect

from . import base, singleton

app, host = singleton.app, singleton.host

import traceback


@app.on_event("startup")
async def startup_event():
    await host.mount()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    try:
        print('Accepting Websocket')
        return await host.accept_socket(websocket, client_id)
    except Exception as err:

        print('An error occured:', str(err))
        traceback.print_exc()
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
    await host.disconnect(websocket)
