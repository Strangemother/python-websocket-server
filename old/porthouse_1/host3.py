import sys
from pathlib import Path
from typing import List

from .ingress import app

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .house import connection
from . import home, state


class Broadcast(state.MicroState):
    name = 'broadcast'

    def mount(self, state_machine, index=-1, parent=None):
        self.ids = {}
        return super().mount(state_machine, index, parent)


    async def inbound(self, owner, last_data=None):
        _id = id(owner)
        self.ids[_id] = owner
        print('\n  broadcast.entry client', _id, '\n')
        # keep open, new val == True
        return 1, True

    async def entry(self, data, owner, micro_position):
        return await self.msg_in(data, owner, micro_position)

    async def concurrent(self, data, owner, micro_position):
        return await self.msg_in(data, owner, micro_position)

    async def msg_in(self, data, owner, micro_position):
        move_on = False
        client_count = len(self.ids)
        print(f'\nMessage in for {client_count}', data,'\n')
        _id = id(owner)
        d = {'from': _id,
            'content': data,
            'position': micro_position,
            'client_count': client_count
            }
        for wid, ws in self.ids.items():
            if wid == _id:
                continue
            await ws.send_json(d)

        return move_on, True

    def drop(self, socket_id):
        print('\n  broadcast.drop client', socket_id, '\n')
        del self.ids[socket_id]


class DropCapture(object):

    async def initial_entry(self, owner):
        return True

    async def push_message(self, data, owner):
        print('  Envelope', data)
        return data

    async def disconnecting_socket(self, websocket, client_id, error):
        broadcast_room.drop(id(websocket))


broadcast_room = Broadcast()

# These plugins define the procedural list a single client should
# walk. Each step is like a function - but built with an async waiting.
plugins = ()
envelopes = ( DropCapture(), )
entry_acceptors = ( broadcast_room,)


state_machine = state.StateMachine(plugins,
        entry_acceptors=entry_acceptors,
        envelopes=envelopes,
    )

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
