from __future__ import annotations

import logging
import time
from abc import abstractmethod
from asyncio import Lock
from typing import Callable

from peaqevcore.common.models.observer_types import ObserverTypes

from custom_components.peaqev.peaqservice.observer.const import (
    COMMAND_WAIT, TIMEOUT)
from custom_components.peaqev.peaqservice.observer.models.command import \
    Command
from custom_components.peaqev.peaqservice.observer.models.observer_model import \
    ObserverModel

_LOGGER = logging.getLogger(__name__)


class IObserver:
    """
    Observer class handles updates throughout peaqev.
    Attach to hub class and subscribe to updates (string matches) in other classes connected to the hub.
    When broadcasting, you may use one argument that the of-course needs to correspond to your receiving function.
    """

    def __init__(self):
        self.model = ObserverModel()
        self._lock = Lock()

    def activate(self, init_broadcast: ObserverTypes = None) -> None:
        self.model.active = True
        if init_broadcast is not None:
            self.broadcast(init_broadcast)

    def deactivate(self) -> None:
        self.model.active = False

    def _check_and_convert_enum_type(self, command) -> str:
        if isinstance(command, ObserverTypes):
            return command.value
        return command

    def add(self, event: ObserverTypes | str, func):
        event = self._check_and_convert_enum_type(event)
        if event in self.model.subscribers.keys():
            self.model.subscribers[event].append(func)
        else:
            self.model.subscribers[event] = [func]

    async def async_broadcast(self, event: ObserverTypes | str, argument=None):
        self.broadcast(event, argument)
        if len(self.model.broadcast_queue) > 10:
            await self.async_dispatch()

    def broadcast(self, command: ObserverTypes | str, argument=None):
        command = self._check_and_convert_enum_type(command)
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
                for func in self.model.subscribers.get(command.command, []):
                    await self.async_broadcast_separator(func, command)
                if command in self.model.broadcast_queue:
                    self.model.broadcast_queue.remove(command)

    @abstractmethod
    async def async_broadcast_separator(self, func, command):
        pass

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
        try:
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
        except Exception as e:
            _LOGGER.error(f'async_call_func for {func} with command {command}: {e}')

    async def async_ok_to_broadcast(self, command) -> bool:
        if command not in self.model.wait_queue.keys():
            self.model.wait_queue[command] = time.time()
            return True
        if time.time() - self.model.wait_queue.get(command, 0) > COMMAND_WAIT:
            self.model.wait_queue[command] = time.time()
            return True
        return False

    def get_state(self, event: ObserverTypes | str):
        event = self._check_and_convert_enum_type(event)
        results = {}
        if event not in self.model.subscribers.keys():
            _LOGGER.warning('No subscribers for event %s that allow get state' % event)
            return None
        for full_path in self.model.subscribers[event]:
            class_name, attr_name = full_path.rsplit('.', 1)
            obj = globals()[class_name]
            if hasattr(obj, attr_name):
                results[full_path] = getattr(obj, attr_name)
        if len(results) == 1:
            return next(iter(results.values()))
        return results

    def set_state(self, event: ObserverTypes|str, value: any) -> bool:
        event = self._check_and_convert_enum_type(event)
        if event in self.model.subscribers.keys():
            for full_path in self.model.subscribers[event]:
                class_name, attr_name = full_path.rsplit('.', 1)
                obj = globals()[class_name]
                if hasattr(obj, attr_name):
                    try:
                        setattr(obj, attr_name, value)
                    except Exception as e:
                        _LOGGER.error(f'set state for {full_path} with value {value}: {e}')
                        return False
        return True
