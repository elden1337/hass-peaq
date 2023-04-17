from __future__ import annotations

import logging
import time
from asyncio import Lock
from datetime import timedelta
from typing import Callable

from homeassistant.helpers.event import async_track_time_interval

from custom_components.peaqev.peaqservice.hub.observer.const import (
    COMMAND_WAIT, TIMEOUT)
from custom_components.peaqev.peaqservice.hub.observer.models.command import \
    Command
from custom_components.peaqev.peaqservice.hub.observer.models.observer_model import \
    ObserverModel
from custom_components.peaqev.peaqservice.util.extensionmethods import \
    async_iscoroutine

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
        self._lock = Lock()
        async_track_time_interval(
            self.hub.state_machine, self.async_dispatch, timedelta(seconds=1)
        )

    def activate(self, init_broadcast: str = None) -> None:
        self.model.active = True
        if init_broadcast is not None:
            self.broadcast(init_broadcast)

    def deactivate(self) -> None:
        self.model.active = False

    def add(self, command: str, func):
        if command in self.model.subscribers.keys():
            self.model.subscribers[command].append(func)
        else:
            self.model.subscribers[command] = [func]

    async def async_broadcast(self, command: str, argument=None):
        await self.hub.state_machine.async_add_executor_job(
            self.broadcast, command, argument
        )

    def broadcast(self, command: str, argument=None):
        _expiration = time.time() + TIMEOUT
        cc = Command(command, _expiration, argument)
        if cc not in self.model.broadcast_queue:
            self.model.broadcast_queue.append(cc)

    async def async_dispatch(self, *args):
        q: Command
        for q in self.model.broadcast_queue:
            if q.command in self.model.subscribers.keys():
                await self.async_dequeue_and_broadcast(q)

    async def async_dequeue_and_broadcast(self, command: Command):
        if await self.async_ok_to_broadcast(command.command):
            async with self._lock:
                _LOGGER.debug(
                    f"ready to broadcast: {command.command} with params: {command.argument}"
                )
                for func in self.model.subscribers[command.command]:
                    if await async_iscoroutine(func):
                        await self.async_call_func(func=func, command=command),
                    else:
                        await self.hub.state_machine.async_add_executor_job(
                            self._call_func, func, command
                        )
                self.model.broadcast_queue.remove(command)

    @staticmethod
    def _call_func(func: Callable, command: Command) -> None:
        if command.argument is not None:
            if isinstance(command.argument, dict):
                try:
                    func(**command.argument)
                except TypeError:
                    func()
            else:
                try:
                    func(command.argument)
                except TypeError:
                    func()
        else:
            func()

    @staticmethod
    async def async_call_func(func: Callable, command: Command) -> None:
        if command.argument is not None:
            if isinstance(command.argument, dict):
                try:
                    await func(**command.argument)
                except TypeError:
                    await func()
            else:
                try:
                    await func(command.argument)
                except TypeError:
                    await func()
        else:
            await func()

    async def async_ok_to_broadcast(self, command) -> bool:
        if command not in self.model.wait_queue.keys():
            self.model.wait_queue[command] = time.time()
            return True
        if time.time() - self.model.wait_queue.get(command, 0) > COMMAND_WAIT:
            self.model.wait_queue[command] = time.time()
            return True
        return False
