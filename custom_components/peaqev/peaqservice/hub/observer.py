from __future__ import annotations

import logging
import time
from typing import Tuple

_LOGGER = logging.getLogger(__name__)
COMMAND_WAIT = 3
TIMEOUT = 60


class Observer:
    def __init__(self, hub):
        self._subscribers: dict = {}
        self._broadcast_queue = []
        self._wait_queue = {}
        self._active = False
        self.hub = hub

    def activate(self) -> None:
        self._active = True

    def add(self, command: str, func):
        if command in self._subscribers.keys():
            self._subscribers[command].append(func)
        else:
            self._subscribers[command] = [func]

    def broadcast(self, command: str, argument=None):
        _expiration = time.time() + TIMEOUT
        if (command, _expiration) not in self._broadcast_queue:
            self._broadcast_queue.append((command, _expiration, argument))
        for q in self._broadcast_queue:
            if q[0] in self._subscribers.keys():
                self._dequeue_and_broadcast(q)
        #self._prepare_dequeue()

    def _prepare_dequeue(self, attempt:int = 0) -> None:
        if self._active:
            for q in self._broadcast_queue:
                if q[0] in self._subscribers.keys():
                    self._dequeue_and_broadcast(q)
        elif attempt < 5:
            _ = self.hub.is_initialized
            attempt += 1
            return self._prepare_dequeue(attempt)

    def _dequeue_and_broadcast(self, command: Tuple[str, int, any]):
        _LOGGER.debug(f"ready to broadcast: {command[0]}")
        if self._ok_to_broadcast(command[0]):
            if command[1] > time.time():
                for func in self._subscribers[command[0]]:
                    if len(command) == 3:
                        func(command[2])
                    else:
                        func()
            self._broadcast_queue.remove(command)

    def _ok_to_broadcast(self, command) -> bool:
        if command not in self._wait_queue.keys():
            self._wait_queue[command] = time.time()
            return True
        if time.time() - self._wait_queue[command] > COMMAND_WAIT:
            self._wait_queue[command] = time.time()
            return True
        return False
