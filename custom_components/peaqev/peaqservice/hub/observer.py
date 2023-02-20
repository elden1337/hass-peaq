from __future__ import annotations

import logging
import time
from typing import Tuple

_LOGGER = logging.getLogger(__name__)


class Observer:
    def __init__(self, hub):
        self._subscribers: dict = {}
        self._queue = []
        self.hub = hub

    def add(self, command: str, func):
        if command in self._subscribers.keys():
            self._subscribers[command].append(func)
        else:
            self._subscribers[command] = [func]

    def broadcast(self, command: str, timeout: int = None):
        _expires = None
        if timeout is not None:
            _expires = time.time() + timeout
        if (command, _expires) not in self._queue:
            self._queue.append((command, _expires))
        if self.hub.is_initialized:
            for q in self._queue:
                if q[0] in self._subscribers.keys():
                    self._dequeue_and_broadcast(q)

    def _dequeue_and_broadcast(self, command: Tuple[str, int|None]):
        _LOGGER.debug(f"ready to broadcast: {command[0]}")
        if command[1] is None or command[1] > time.time():
            for func in self._subscribers[command[0]]:
                func()
        self._queue.remove(command)
