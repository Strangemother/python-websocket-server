from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import json
from functools import lru_cache
import events
from message import easy_send


class Packet(object):
    """A message from external converted to an internal message, ready for
    digest through the waiting components.

    It's mostly a convenience tool to replace the str, or JSON message within
    the app. Generally call `Packet.get_json` to gather a dict object of
    the `message`.

    Use `as_model` or `as_event(name)` to convert into an internal event lib
    format.

    The `owner` is the _incoming_ owning `Websocket` of the Packet.
    """

    def __init__(self, message: str, owner: WebSocket, uuid:None):
        self.message = message
        self.owner = owner
        self.json = None
        self.uuid = uuid

    @lru_cache(maxsize=32)
    def as_model(self):
        """Return the model associated with the event type.
        """
        return events.convert_packet(self)

    def as_event(self, name):
        """Nonimate this packet as an _event_ and cast as the given named
        event model. Return a Model type from events.

            Model = Packet('{"unit": "world"}').as_event('NewScene')
        """
        return events.convert(self, name)

    def get_json(self):
        if self.json is None:
            self.json = self.convert()
        return self.json

    as_json = get_json

    def convert(self):
        """Convert the internal message to the dict format for application
        digest.
        """
        if self.is_json():
            return self._from_json()
        return self._from_text()

    def __getitem__(self, k):
        return self.convert().get(k)

    def _from_json(self):
        try:
            return json.loads(self.message)
        except json.JSONDecodeError as e:
            return { 'text': self.message}

    def _from_text(self):
        """Convert the special packet into a json dict.
        """
        # raise NotImplemented()
        return {"text": self.message}

    def is_json(self):
        m = self.message
        return len(m) > 1 and (m[0] == '{' and m[-1] == '}')

    async def respond_json(self, **content):
        to = self.owner
        if "to" in content:
            print('Using content target "to"', content['to'])
            to = content.pop('to')

        return await easy_send(to=to,
                **content
            )

    def __str__(self):
        return f"Packet({self.uuid}): {self.message}"
