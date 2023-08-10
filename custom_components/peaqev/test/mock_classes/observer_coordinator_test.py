from __future__ import annotations

import asyncio

from custom_components.peaqev.peaqservice.hub.observer.iobserver_coordinator import \
    IObserver
from custom_components.peaqev.peaqservice.util.extensionmethods import \
    async_iscoroutine


class ObserverTest(IObserver):
    def __init__(self):
        super().__init__()

    async def async_broadcast_separator(self, func, command):
        if await async_iscoroutine(func):
            await self.async_call_func(func=func, command=command),
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._call_func, func, command)
