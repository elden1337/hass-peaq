from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.helpers.event import async_track_time_interval

from custom_components.peaqev.peaqservice.hub.observer.iobserver_coordinator import \
    IObserver
from custom_components.peaqev.peaqservice.hub.observer.models.command import \
    Command
from custom_components.peaqev.peaqservice.util.extensionmethods import \
    async_iscoroutine

_LOGGER = logging.getLogger(__name__)


class Observer(IObserver):
    def __init__(self, hass, entry=None):
        super().__init__()
        self.hass = hass
        unsub = async_track_time_interval(
            self.hass, self.async_dispatch, timedelta(seconds=1),
            cancel_on_shutdown=True,
        )
        if entry is not None:
            entry.async_on_unload(unsub)
        else:
            self._unsub = unsub

    async def async_broadcast_separator(self, func, command: Command):
        if await async_iscoroutine(func):
            await self.async_call_func(func=func, command=command),
        else:
            await self.hass.async_add_executor_job(
                self._call_func, func, command
            )
