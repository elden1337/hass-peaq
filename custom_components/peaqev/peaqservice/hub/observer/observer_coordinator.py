from __future__ import annotations

import asyncio
import logging
import time

from custom_components.peaqev.peaqservice.hub.observer.const import TIMEOUT, COMMAND_WAIT
from custom_components.peaqev.peaqservice.hub.observer.models.command import Command
from custom_components.peaqev.peaqservice.hub.observer.models.function_call import FunctionCall
from custom_components.peaqev.peaqservice.hub.observer.models.observer_model import ObserverModel

_LOGGER = logging.getLogger(__name__)


class Observer:
    """
    Observer class handles updates throughout peaqev.
    Attach to hub class and subscribe to updates (string matches) in other classes connected to the hub.
    When broadcasting, you may use one argument that the of-course needs to correspond to your receiving function.
    """

    def __init__(self, hub):
        self.model = ObserverModel()
        self.hub = hub

    def activate(self, init_broadcast: str = None) -> None:
        self.model.active = True
        if init_broadcast is not None:
            self.broadcast(init_broadcast)

    def deactivate(self) -> None:
        self.model.active = False

    def add(self, command: str, func, _async: bool = False):
        if command in self.model.subscribers.keys():
            self.model.subscribers[command].append(FunctionCall(func, _async))
        else:
            self.model.subscribers[command] = [FunctionCall(func, _async)]

    async def async_broadcast(self, command: str, argument=None):
        await self.hub.state_machine.async_add_executor_job(self.broadcast, command, argument)

    def broadcast(self, command: str, argument=None):
        _expiration = time.time() + TIMEOUT
        cc = Command(command, _expiration, argument)
        if cc not in self.model.broadcast_queue:
            self.model.broadcast_queue.append(cc)
        #if self.model.active:
        q: Command
        for q in self.model.broadcast_queue:
            if q.command in self.model.subscribers.keys():
                self._dequeue_and_broadcast(q)

    def _dequeue_and_broadcast(self, command: Command):
        _LOGGER.debug(f"ready to broadcast: {command.command} with params: {command.argument}")
        if self._ok_to_broadcast(command.command):
            if command.expiration > time.time():
                func: FunctionCall
                for func in self.model.subscribers[command.command]:
                    if func.call_async:
                        _ = asyncio.run_coroutine_threadsafe(
                            self.async_call_func(func.function, command), self.hub.state_machine.loop
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
