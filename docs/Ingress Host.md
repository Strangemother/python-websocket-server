# The Ingress

The Ingress or 'host' asynchronously serve the websockets to the connection manager.
In an example using FastAPI:

```py
from porthouse.house import connection
from porthouse import home, state

state_machine = state.StateMachine()
con_manager = connection.Manager(state_machine)

globals()['app'] = app


@app.on_event("startup")
async def startup_event():
    """Run the host manager within the async for await tools"""
    await con_manager.mount()


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
```

If the ingress endpoint is the same as the connection manager, you may simply decorate the ingress methods to save some keystrokes:

```py
app.websocket("/")(con_manager.master_ingress)
app.websocket("/{user_uuid}/")(con_manager.uuid_ingress)
```
