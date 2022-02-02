import json
from fastapi import WebSocket


async def easy_send(to, **kwargs):
    """An "easy to use" function with one required param `to`, as a iterable
    or client, or client ID. Provide a range of `kwargs`, automatically
    stringified as a JSON message.

        await easy_send(to=packet.owner,
            event='welcome',
            friendly='Howdy.',
            nominated='client',
            id=packet.owner.uuid,
            scenes=register.scene_list())

    """
    if not isinstance(to, (list, tuple,)):
        to = (to,)

    for client in to:
        if isinstance(client, WebSocket):
            await client.send_json(kwargs)
