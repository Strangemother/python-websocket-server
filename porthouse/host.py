import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .ingress import app
from .house import connection
from . import home, state




class Forever(state.MicroState):
    async def concurrent(self, data, owner, micro_position):
        print('F:', data)
        move_on = data.get('text', '').lower() == 'thanks'
        return move_on, True


class Debug(state.KeyMicroState):

    name = 'debug'

    async def push_state_message(self, micro_position, data, owner):
        move_on = False
        micro_val = 2
        import pdb; pdb.set_trace()  # breakpoint 72df0baa //

        return move_on, micro_val


class HotMove(state.KeyMicroState):

    async def push_state_message(self, micro_position, data, owner):
        t = data.get('text', None)
        if t == self.kwargs.get('text'):
            self.release()
        # move_on, micro_position inc
        return False, True


class EmitRelease(state.KeyMicroState):
    async def push_state_message(self, micro_position, data, owner):
        if (micro_position or 0) > 2:
            raise state.Release()
        return False, True


# These plugins define the procedural list a single client should
# walk. Each step is like a function - but built with an async waiting.
plugins = (
    state.MicroState(name='BEFORE'),
    state.KeyMicroState(name='beta', move_to='other', init_value=-3),
    state.KeyLobby(name='keyarea',
        # state_index=0,
        acceptors=(
            state.MicroState(name='egg'),
            HotMove(name='fred', text='egg', move_to='cake'),
            state.KeyMicroState(name='beta', move_to='delta', init_value=-3),
            state.MicroState(name='charlie'),
            state.KeyMicroState(name='delta', move_to='charlie'),
            state.KeyMicroState(name='cake', move_to='debug'),
            Debug(),
        )
     ),
    state.KeyMicroState(name='other', move_to='keyarea', init_value=1),
    state.Lobby(name='area',
        # state_index=0,
        acceptors=(
            Forever(name='FOREVER'),
        )
     ),
)


state_machine = state.StateMachine(plugins,
        entry_acceptors=(
            EmitRelease(name='EmitRelease'),
            # state.MicroState(name='alpha'),
            # state.MicroState(name='beta'),
        )
    )


# state_machine = state.MicroMachine()

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
