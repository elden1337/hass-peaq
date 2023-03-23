import asyncio
import logging
from datetime import datetime
from statistics import mean

import homeassistant.helpers.template as template

from custom_components.peaqev.peaqservice.hub.nordpool.nordpool_dto import NordpoolDTO
from custom_components.peaqev.peaqservice.hub.nordpool.nordpool_model import NordPoolModel

_LOGGER = logging.getLogger(__name__)

NORDPOOL = "nordpool"
AVERAGE_MAX_LEN = 31


class NordPoolUpdater:
    def __init__(self, hub, is_active: bool = True):
        self.model = NordPoolModel()
        self.hub = hub
        self._nordpool_entity:str = None
        if is_active:
            self._setup_nordpool()

    @property
    def currency(self) -> str:
        return self.model.currency

    @property
    def state(self) -> float:
        return self.model.state

    @state.setter
    def state(self, val) -> None:
        if self.model.state != val:
            self.model.state = val

    @property
    def average_month(self) -> float:
        return self.model.average_month

    @property
    def average_weekly(self) -> float:
        return self.model.average_weekly

    @property
    def average_data(self) -> list:
        return self.model.average_data

    @property
    def average_ready(self) -> bool:
        return len(self.model.average_data) >= AVERAGE_MAX_LEN

    async def update_nordpool(self):
        if self._nordpool_entity is not None:
            ret = self.hub.state_machine.states.get(self._nordpool_entity)
            _result = NordpoolDTO()
            if ret is not None:
                await _result.set_model(ret)
                if await self._update_set_prices(_result):
                    await self.hub.observer.async_broadcast("prices changed",[self.model.prices, self.model.prices_tomorrow])
            elif self.hub.is_initialized:
                _LOGGER.error("Could not get nordpool-prices")

    async def _update_average_month(self) -> None:
        _new = await self._get_average_async(datetime.now().day)
        if len(self.model.average_data) > 0 and self.model.average_month != _new:
            self.model.average_month = _new
            await self.hub.observer.async_broadcast("monthly average price changed", self.model.average_month)

    async def _update_average_week(self) -> None:
        _average7 = await self._get_average_async(7)
        if len(self.model.average_data) > 0 and self.model.average_weekly != _average7:
            self.model.average_weekly = _average7
            await self.hub.observer.async_broadcast("weekly average price changed", self.model.average_weekly)

    async def _update_average_day(self, average) -> None:
        if average != self.model.daily_average:
            self.model.daily_average = average
            await self._add_average_data(average)
            await self.hub.observer.async_broadcast("daily average price changed", average)

    async def _update_set_prices(self, result: NordpoolDTO) -> bool:
        ret = False
        if self.model.prices != result.today:
            self.model.prices = result.today
            ret = True
        if self.model.prices_tomorrow != result.tomorrow:
            self.model.prices_tomorrow = result.tomorrow
            ret = True
        await self._update_average_week()
        self.model.currency = result.currency
        self.state = result.state
        await self._update_average_day(result.average)
        await self._update_average_month()
        return ret

    def _setup_nordpool(self):
        try:
            entities = template.integration_entities(self.hub.state_machine, NORDPOOL)
            if len(list(entities)) < 1:
                raise Exception("no entities found for Nordpool.")
            if len(list(entities)) == 1:
                self._nordpool_entity = entities[0]
                _LOGGER.debug(f"Nordpool has been set up and is ready to be used with {self._nordpool_entity}")
                asyncio.run_coroutine_threadsafe(
                    self.update_nordpool(), self.hub.state_machine.loop
                )
            else:
                self.hub.options.price.price_aware = False  # todo: composition
                _LOGGER.error(f"more than one Nordpool entity found. Disabling Priceawareness until reboot of HA.")
        except Exception as e:
            self.hub.options.price.price_aware = False  # todo: composition
            _LOGGER.error(f"Peaqev was unable to get a Nordpool-entity. Disabling Priceawareness until reboot of HA: {e}")

    async def import_average_data(self, incoming: list):
        if isinstance(incoming, list):
            rounded_vals = [round(h, 3) for h in incoming]
            if len(incoming):
                self.model.average_data = rounded_vals
        await self._cap_average_data_length()

    async def _add_average_data(self, new_val):
        if isinstance(new_val, float):
            rounded = round(new_val, 3)
            if len(self.model.average_data) == 0:
                self.model.average_data.append(rounded)
            elif self.model.average_data[-1] != rounded:
                self.model.average_data.append(rounded)
            await self._cap_average_data_length()

    async def _cap_average_data_length(self):
        while len(self.model.average_data) > AVERAGE_MAX_LEN:
            del self.model.average_data[0]

    async def _get_average_async(self, days: int) -> float:
        try:
            if len(self.model.average_data) > days:
                ret = self.model.average_data[-days:]
            elif len(self.model.average_data) == 0:
                return 0.0
            else:
                ret = self.model.average_data
            return round(mean(ret), 2)
        except Exception as e:
            _LOGGER.debug(f"Could not calculate average. indata: {self.model.average_data}, error: {e}")
