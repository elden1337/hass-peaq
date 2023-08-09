from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.helpers.event import async_track_time_interval

from custom_components.peaqev.peaqservice.hub.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.util.extensionmethods import \
    async_iscoroutine

_LOGGER = logging.getLogger(__name__)


class Observer(IObserver):
    def __init__(self, hub):
        super().__init__()
        self.hub = hub
        async_track_time_interval(
            self.hub.state_machine, self.async_dispatch, timedelta(seconds=1)
        )

    async def async_broadcast_separator(self, func, command):
        if await async_iscoroutine(func):
            await self.async_call_func(func=func, command=command),
        else:
            await self.hub.state_machine.async_add_executor_job(
                self._call_func, func, command
            )


import asyncio

class ObserverTest(IObserver):
    def __init__(self):
        super().__init__()

    async def async_broadcast_separator(self, func, command):
        if await async_iscoroutine(func):
            await self.async_call_func(func=func, command=command),
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._call_func, func, command)
