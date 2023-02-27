from __future__ import annotations

import logging
import time
from typing import Tuple

_LOGGER = logging.getLogger(__name__)
COMMAND_WAIT = 3


class Observer:
    def __init__(self, hub):
        self._subscribers: dict = {}
        self._broadcast_queue = []
        self._wait_queue = {}
        self.hub = hub

    def add(self, command: str, func):
        if command in self._subscribers.keys():
            self._subscribers[command].append(func)
        else:
            self._subscribers[command] = [func]

    def broadcast(self, command: str, timeout: int = None):
        _expiration = None
        if timeout is not None:
            _expiration = time.time() + timeout
        if (command, _expiration) not in self._broadcast_queue:
            self._broadcast_queue.append((command, _expiration))
        for q in self._broadcast_queue:
            if q[0] in self._subscribers.keys():
                self._dequeue_and_broadcast(q)

    def _ok_to_broadcast(self, command) -> bool:
        if command not in self._wait_queue.keys():
            self._wait_queue[command] = time.time()
            return True
        if time.time() - self._wait_queue[command] > COMMAND_WAIT:
            self._wait_queue[command] = time.time()
            return True
        return False

    def _dequeue_and_broadcast(self, command: Tuple[str, int | None]):
        _LOGGER.debug(f"ready to broadcast: {command[0]}")
        if command[1] is None or command[1] > time.time():
            if self._ok_to_broadcast(command[0]):
                for func in self._subscribers[command[0]]:
                    func()
                self._broadcast_queue.remove(command)
