from copy import deepcopy
import io
import json

from world_trader.models import Document

NOW = "2026-10-19T04:00:00.000000Z"


class FakeClient:
    def __init__(self, *payloads):
        self.payloads = list(payloads)
        self.calls = []

    def timestamp(self):
        return NOW

    def get(self, url, **kwargs):
        self.calls.append((url, deepcopy(kwargs)))
        return Document(deepcopy(self.payloads.pop(0)), NOW, url, "a" * 64)


class Clock:
    def __init__(self):
        self.now = 1780000000.0
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, amount):
        self.sleeps.append(amount)
        self.now += amount


class Opener:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, req, **kwargs):
        self.calls.append((req, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return io.BytesIO(response if isinstance(response, bytes) else json.dumps(response).encode())
