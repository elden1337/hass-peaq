import logging
from statistics import mean

import homeassistant.helpers.template as template

from custom_components.peaqev.peaqservice.hub.nordpool.nordpool_model import NordPoolModel

_LOGGER = logging.getLogger(__name__)

NORDPOOL = "nordpool"
AVERAGE_MAX_LEN = 31


class NordPoolUpdater:
    def __init__(self, hass, hub, is_active: bool = True):
        self.model = NordPoolModel()
        self._hass = hass
        self._hub = hub
        if is_active:
            self._setup_nordpool()

    @property
    def currency(self) -> str:
        return self.model.currency

    @property
    def prices(self) -> list:
        return self.model.prices

    @property
    def prices_tomorrow(self) -> list:
        return self.model.prices_tomorrow

    @property
    def state(self) -> float:
        return self.model.state

    @property
    def average_data(self) -> list:
        return self.model.average_data

    @property
    def average_ready(self) -> bool:
        return len(self.model.average_data) >= AVERAGE_MAX_LEN

    async def update_nordpool(self):
        ret = self._hass.states.get(self.nordpool_entity)
        if ret is not None:
            try:
                ret_attr = list(ret.attributes.get("today"))
                self.model.prices = ret_attr
            except Exception as e:
                _LOGGER.exception(f"Could not parse today's prices from Nordpool. Unsolveable error. {e}")
                return
            try:
                ret_attr_tomorrow = list(ret.attributes.get("tomorrow"))
                self.model.prices_tomorrow = ret_attr_tomorrow
            except Exception as e:
                _LOGGER.warning(f"Couldn't parse tomorrow's prices from Nordpool. Array will be empty. {e}")
                self.model.prices_tomorrow = []
            ret_attr_currency = str(ret.attributes.get("currency"))
            self.model.currency = ret_attr_currency
            self.model.state = ret.state
            try:
                _avg_data = str(ret.attributes.get("average"))
                self.add_average_data(float(_avg_data))
            except Exception as ee:
                _LOGGER.warning(f"Could not parse today's average from Nordpool. {ee}")
            await self._update_set_prices()
        elif self._hub.is_initialized:
            _LOGGER.error("Could not get nordpool-prices")

    async def _update_set_prices(self) -> None:
        if self._hub.hours.prices != self.model.prices:
            self._hub.hours.prices = self.model.prices
        if self._hub.hours.prices_tomorrow != self.model.prices_tomorrow:
            self._hub.hours.prices_tomorrow = self.model.prices_tomorrow
        if len(self.model.average_data) >= 7 and self._hub.hours.adjusted_average != self.get_average(7):
            self._hub.hours.adjusted_average = self.get_average(7)

    def _setup_nordpool(self):
        try:
            entities = template.integration_entities(self._hass, NORDPOOL)
            if len(entities) < 1:
                raise Exception("no entities found for Nordpool.")
            if len(entities) == 1:
                self.nordpool_entity = entities[0]
                _LOGGER.debug(f"Nordpool has been set up and is ready to be used with {self.nordpool_entity}")
                self.update_nordpool()
            else:
                self._hub.options.price.price_aware = False
                _LOGGER.error(f"more than one Nordpool entity found. Disabling Priceawareness until reboot of HA.")
        except Exception as e:
            self._hub.options.price.price_aware = False
            _LOGGER.error(
                f"Peaqev was unable to get a Nordpool-entity. Disabling Priceawareness until reboot of HA: {e}")

    def import_average_data(self, incoming: list):
        if isinstance(incoming, list):
            rounded_vals = [round(h, 3) for h in incoming]
            if len(incoming) > 0:
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
