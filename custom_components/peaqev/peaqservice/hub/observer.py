from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Tuple

_LOGGER = logging.getLogger(__name__)
COMMAND_WAIT = 3
TIMEOUT = 60


@dataclass
class ObserverModel:
    subscribers: dict = field(default_factory=lambda: {})
    broadcast_queue: list = field(default_factory=lambda: [])
    wait_queue: dict = field(default_factory=lambda: {})
    active: bool = False


@dataclass
class Command:
    command: str
    expiration: int = None
    argument: any = None


@dataclass
class Func:
    function: any
    call_async: bool = False

class Observer:
    """
    Observer class handles updates throughout peaqev.
    Attach to hub class and subscribe to updates (string matches) in other classes connected to the hub.
    When broadcasting, you may use one argument that the of-course needs to correspond to your receiving function.
    """

    def __init__(self, hub):
        self.model = ObserverModel()
        self.hub = hub

    def activate(self) -> None:
        self.model.active = True

    def deactivate(self) -> None:
        self.model.active = False

    def add(self, command: str, func, _async: bool = False):
        if command in self.model.subscribers.keys():
            self.model.subscribers[command].append(Func(func, _async))
        else:
            self.model.subscribers[command] = [Func(func, _async)]

    async def async_broadcast(self, command: str, argument=None):
            await self.hub.state_machine.async_add_executor_job(self.broadcast, command, argument)

    def broadcast(self, command: str, argument=None):
        _expiration = time.time() + TIMEOUT
        if (command, _expiration) not in self.model.broadcast_queue:
            self.model.broadcast_queue.append(Command(command, _expiration, argument))
        q: Command
        for q in self.model.broadcast_queue:
            if q.command in self.model.subscribers.keys():
                self._dequeue_and_broadcast(q)
        #self._prepare_dequeue()

    # def _prepare_dequeue(self, attempt: int = 0) -> None:
    #     if self.model.active:
    #         for q in self.model.broadcast_queue:
    #             if q[0] in self.model.subscribers.keys():
    #                 self._dequeue_and_broadcast(q)
    #     elif attempt < 5:
    #         _ = self.hub.is_initialized
    #         attempt += 1
    #         return self._prepare_dequeue(attempt)

    def _dequeue_and_broadcast(self, command: Command):
        _LOGGER.debug(f"ready to broadcast: {command.command} with params: {command.argument}")
        if self._ok_to_broadcast(command.command):
            if command.expiration > time.time():
                func: Func
                for func in self.model.subscribers[command.command]:
                    if func.call_async:
                        _ = asyncio.run_coroutine_threadsafe(
                            self.async_call_func(func.function,command), self.hub.state_machine.loop
                        ).result()
                    else:
                        self._call_func(func.function, command)
            self.model.broadcast_queue.remove(command)

    @staticmethod
    def _call_func(func, command: Command):
        if command.argument is not None:
            if isinstance(command.argument, dict):
                func(**command.argument)
            else:
                func(command.argument)
        else:
            func()

    @staticmethod
    async def async_call_func(func, command: Command):
        if command.argument is not None:
            if isinstance(command.argument, dict):
                await func(**command.argument)
            else:
                await func(command.argument)
        else:
            await func()

    def _ok_to_broadcast(self, command) -> bool:
        if command not in self.model.wait_queue.keys():
            self.model.wait_queue[command] = time.time()
            return True
        if time.time() - self.model.wait_queue.get(command) > COMMAND_WAIT:
            self.model.wait_queue[command] = time.time()
            return True
        return False
