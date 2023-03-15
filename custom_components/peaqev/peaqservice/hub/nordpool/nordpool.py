import logging
from datetime import datetime
from statistics import mean

import homeassistant.helpers.template as template

from custom_components.peaqev.peaqservice.hub.nordpool.nordpool_model import NordPoolModel

_LOGGER = logging.getLogger(__name__)

NORDPOOL = "nordpool"
AVERAGE_MAX_LEN = 31


class NordPoolUpdater:
    def __init__(self, hub, is_active: bool = True):
        self.model = NordPoolModel()
        self.hub = hub
        if is_active:
            self._setup_nordpool()

    @property
    def currency(self) -> str:
        return self.model.currency

    # @property
    # def prices(self) -> list:
    #     return self.model.prices
    #
    # @prices.setter
    # def prices(self, val) -> None:
    #     if self.model.prices != val:
    #         self.model.prices = val

    # @property
    # def prices_tomorrow(self) -> list:
    #     return self.model.prices_tomorrow

    # @prices_tomorrow.setter
    # def prices_tomorrow(self, val) -> None:
    #     if self.model.prices_tomorrow != val:
    #         self.model.prices_tomorrow = val

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
        ret = self.hub.state_machine.states.get(self.nordpool_entity)
        _result = {}
        if ret is not None:
            try:
                _result["today"] = list(ret.attributes.get("today"))
            except Exception as e:
                _LOGGER.exception(f"Could not parse today's prices from Nordpool. Unsolveable error. {e}")
                return
            try:
                _result["tomorrow"] = list(ret.attributes.get("tomorrow"))
            except Exception as e:
                _LOGGER.warning(f"Couldn't parse tomorrow's prices from Nordpool. Array will be empty. {e}")
                _result["tomorrow"] = []
            _result["currency"] = str(ret.attributes.get("currency"))
            _result["state"] = ret.state
            try:
                _avg_data = float(str(ret.attributes.get("average")))
                _result["avg_data"] = _avg_data
            except Exception as ee:
                _LOGGER.warning(f"Could not parse today's average from Nordpool. exception: {ee}")
            if await self._update_set_prices(_result):
                self.hub.observer.broadcast("prices changed", [self.model.prices, self.model.prices_tomorrow])
        elif self.hub.is_initialized:
            _LOGGER.error("Could not get nordpool-prices")

    def _update_average_month(self) -> None:
        _new = self.get_average(datetime.now().day)
        if self.model.average_month != _new:
            self.model.average_month = _new
            self.hub.observer.broadcast("monthly average price changed", self.model.average_month)

    async def _update_set_prices(self, result: dict) -> bool:
        ret = False
        if self.model.prices != result.get("today"):
            self.model.prices = result.get("today")
            ret = True
        if self.model.prices_tomorrow != result.get("tomorrow"):
            self.model.prices_tomorrow = result.get("tomorrow")
            ret = True
        if len(self.model.average_data) >= 7 and self.model.average_weekly != self.get_average(7):
            self.model.average_weekly = self.get_average(7)
            self.hub.observer.broadcast("weekly average price changed", self.model.average_weekly)
        self.model.currency = result.get("currency")
        self.state = result.get("state")
        if "avg_data" in result.keys():
            daily_avg = result.get("avg_data")
            self.add_average_data(daily_avg)
            self.hub.observer.broadcast("daily average price changed", daily_avg)
            self._update_average_month()
        return ret

    def _setup_nordpool(self):
        try:
            entities = template.integration_entities(self.hub.state_machine, NORDPOOL)
            if len(list(entities)) < 1:
                raise Exception("no entities found for Nordpool.")
            if len(list(entities)) == 1:
                self.nordpool_entity = entities[0]
                _LOGGER.debug(f"Nordpool has been set up and is ready to be used with {self.nordpool_entity}")
                self.update_nordpool()
            else:
                self.hub.options.price.price_aware = False  # todo: composition
                _LOGGER.error(f"more than one Nordpool entity found. Disabling Priceawareness until reboot of HA.")
        except Exception as e:
            self.hub.options.price.price_aware = False  # todo: composition
            _LOGGER.error(f"Peaqev was unable to get a Nordpool-entity. Disabling Priceawareness until reboot of HA: {e}")

    def import_average_data(self, incoming: list):
        if isinstance(incoming, list):
            rounded_vals = [round(h, 3) for h in incoming]
            if len(incoming):
                self.model.average_data = rounded_vals
        self._cap_average_data_length()

    def add_average_data(self, new_val):
        if isinstance(new_val, float):
            rounded = round(new_val, 3)
            if len(self.model.average_data) == 0:
                self.model.average_data.append(rounded)
            elif self.model.average_data[-1] != rounded:
                self.model.average_data.append(rounded)
            self._cap_average_data_length()

    def _cap_average_data_length(self):
        while len(self.model.average_data) > AVERAGE_MAX_LEN:
            del self.model.average_data[0]

    def get_average(self, days: int) -> float:
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
