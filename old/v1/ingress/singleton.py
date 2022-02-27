from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import manager
import scene, client, pipes, register


DEVICES = (
        scene.SceneManager,
        client.ClientManager,
        pipes.PipeManager,
        register.RegisterManager,
        manager.BroadcastDevice,
    )

app = FastAPI(host='127.0.0.1')

host = manager.Host(devices=DEVICES)
