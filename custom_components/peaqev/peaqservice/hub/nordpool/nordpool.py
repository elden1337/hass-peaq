import asyncio
import logging
from datetime import datetime, date
from statistics import mean

import homeassistant.helpers.template as template

from custom_components.peaqev.peaqservice.hub.nordpool.dynamic_top_price import \
    DynamicTopPrice
from custom_components.peaqev.peaqservice.hub.nordpool.models.nordpool_dto import \
    NordpoolDTO
from custom_components.peaqev.peaqservice.hub.nordpool.models.nordpool_model import \
    NordPoolModel

_LOGGER = logging.getLogger(__name__)

NORDPOOL = "nordpool"
AVERAGE_MAX_LEN = 31


class NordPoolUpdater:
    def __init__(self, hub, is_active: bool = True):
        self.model = NordPoolModel()
        self.hub = hub
        self.state_machine = hub.state_machine
        self._nordpool_entity: str | None = None
        self._dynamic_top_price = DynamicTopPrice()
        self._is_initialized: bool = False
        if is_active:
            self._setup_nordpool()

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

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
    def average_30(self) -> float:
        return self.model.average_30

    @property
    def average_data(self) -> dict[date,float]:
        return self.model.average_data

    @property
    def nordpool_entity(self) -> str:
        return getattr(self, "_nordpool_entity", "")

    async def async_update_nordpool(self, initial: bool = False) -> None:
        if self.nordpool_entity is not None:
            ret = self.state_machine.states.get(self.nordpool_entity)
            _result = NordpoolDTO()
            if ret is not None:
                await _result.set_model(ret)
                if await self.async_update_set_prices(_result):
                    if initial:
                        await self.hub.async_update_prices(
                            [self.model.prices, self.model.prices_tomorrow]
                        )
                        await self.hub.observer.async_broadcast("nordpool initialized")
                    else:
                        await self.hub.observer.async_broadcast(
                            "prices changed",
                            [self.model.prices, self.model.prices_tomorrow],
                        )
                    self._is_initialized = True
            elif self.hub.is_initialized:
                _LOGGER.debug(
                    f"Could not get nordpool-prices. initial: {initial}. Nordpool-entity: {self.nordpool_entity}"
                )

    async def async_update_average_month(self) -> None:
        _new = await self.async_get_average(datetime.now().day)
        if (
            len(self.model.average_data) >= int(datetime.now().day)
            and self.model.average_month != _new
        ):
            self.model.average_month = _new
            await self.hub.observer.async_broadcast(
                "monthly average price changed", self.model.average_month
            )

    async def async_update_average_30(self) -> None:
        _new = await self.async_get_average(30)
        if self.model.average_30 != _new:
            self.model.average_30 = _new


    async def async_update_average_week(self) -> None:
        _average7 = await self.async_get_average(7)
        if len(self.model.average_data) >= 7 and self.model.average_weekly != _average7:
            self.model.average_weekly = _average7

    async def async_update_average_three_days(self) -> None:
        _average3 = await self.async_get_average(3)
        if len(self.model.average_data) >= 3 and self.model.average_three_days != _average3:
            self.model.average_three_days = _average3
            await self.hub.observer.async_broadcast(
                "adjusted average price changed", self.model.average_three_days
            )

    async def async_update_average_day(self, average) -> None:
        if average != self.model.daily_average:
            self.model.daily_average = average
            await self.async_add_average_data(average)
            await self.hub.observer.async_broadcast(
                "daily average price changed", average
            )

    async def async_update_set_prices(self, result: NordpoolDTO) -> bool:
        ret = False
        today = await self.model.fix_dst(result.today)
        if self.model.prices != today:
            self.model.prices = today
            ret = True
        if result.tomorrow_valid:
            tomorrow = await self.model.fix_dst(result.tomorrow)
            if self.model.prices_tomorrow != tomorrow:
                self.model.prices_tomorrow = tomorrow
                ret = True
        else:
            if self.model.prices_tomorrow:
                self.model.prices_tomorrow = []
                ret = True
        await self.async_update_average_week()
        await self.async_update_average_three_days()
        self.model.currency = result.currency
        self.model.use_cent = result.price_in_cent
        self.state = result.state
        await self.async_update_average_day(result.average)
        await self.async_update_average_month()
        await self.async_update_average_30()
        await self.async_update_dynamic_max_price()
        return ret

    async def async_update_dynamic_max_price(self):
        if len(self.model.average_data) > 3:
            _dynamic_max_price = await self._dynamic_top_price.async_get_max(
                list(self.model.average_data.values())
            )
            if self.model.dynamic_top_price != _dynamic_max_price[0]:
                self.model.dynamic_top_price_type = _dynamic_max_price[1].value
                self.model.dynamic_top_price = _dynamic_max_price[0]
                _LOGGER.debug(_dynamic_max_price)
                await self.hub.observer.async_broadcast(
                    "dynamic max price changed", _dynamic_max_price[0]
                )

    def _setup_nordpool(self):
        try:
            entities = template.integration_entities(self.hub.state_machine, NORDPOOL)
            if len(list(entities)) < 1:
                raise Exception("no entities found for Nordpool.")
            if len(list(entities)) == 1:
                self._nordpool_entity = entities[0]
                _LOGGER.debug(
                    f"Nordpool has been set up and is ready to be used with {self.nordpool_entity}"
                )
                asyncio.run_coroutine_threadsafe(
                    self.async_update_nordpool(initial=True),
                    self.hub.state_machine.loop,
                )
            else:
                self.hub.options.price.price_aware = False  # todo: composition
                _LOGGER.error(
                    f"more than one Nordpool entity found. Disabling Priceawareness until reboot of HA."
                )
        except Exception as e:
            self.hub.options.price.price_aware = False  # todo: composition
            _LOGGER.error(
                f"Peaqev was unable to get a Nordpool-entity. Disabling Priceawareness until reboot of HA: {e}"
            )

    async def async_import_average_data(self, incoming: list|dict):
        if len(incoming):
            self.model.average_data = await self.model.async_create_date_dict(incoming)
        await self.async_cap_average_data_length()
        await self.async_update_nordpool()

    async def async_add_average_data(self, new_val):
        if isinstance(new_val, float):
            rounded = round(new_val, 3)
            if datetime.now().date not in self.model.average_data.keys():
                self.model.average_data[datetime.now().date] = rounded
            # if len(self.model.average_data) == 0:
            #     self.model.average_data.append(rounded)
            # elif self.model.average_data[-1] != rounded:
            #     self.model.average_data.append(rounded)
            await self.async_cap_average_data_length()

    async def async_cap_average_data_length(self):
        while len(self.model.average_data) > AVERAGE_MAX_LEN:
            min_key = min(self.model.average_data.keys())
            del self.model.average_data[min_key]
            #del self.model.average_data[0]

    async def async_get_average(self, days: int) -> float:
        try:
            if len(self.model.average_data) > days:
                avg_values = list(self.model.average_data.values())
                ret = avg_values[-days:]
            elif len(self.model.average_data) == 0:
                return 0.0
            else:
                ret = list(self.model.average_data.values())
            return round(mean(ret), 2)
        except Exception as e:
            _LOGGER.debug(
                f"Could not calculate average. indata: {list(self.model.average_data.values())}, error: {e}"
            )
