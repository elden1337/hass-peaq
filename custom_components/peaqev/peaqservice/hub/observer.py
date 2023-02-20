import logging

_LOGGER = logging.getLogger(__name__)


class Observer:
    def __init__(self):
        self._subscribers: dict = {}
        self._queue = []

    def add(self, command: str, func):
        if command in self._subscribers.keys():
            self._subscribers[command].append(func)
        else:
            self._subscribers[command] = [func]

    def broadcast(self, command: str):
        self._queue.append(command)
        while len(self._queue):
            self._dequeue_and_broadcast(self._queue.pop(0))

    def _dequeue_and_broadcast(self, command: str):
        if command in self._subscribers.keys():
            updates = self._subscribers[command]
            _LOGGER.debug(f"ready to broadcast: {command}")
            if len(updates):
                for func in updates:
                    func()
