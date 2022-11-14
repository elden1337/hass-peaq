import logging
from statistics import mean

import homeassistant.helpers.template as template

_LOGGER = logging.getLogger(__name__)

NORDPOOL = "nordpool"
AVERAGE_MAX_LEN = 31

class NordPoolUpdater:
    def __init__(self, hass, hub, is_active: bool = True):
        self._hass = hass
        self._hub = hub
        self.currency: str = ""
        self.prices: list = []
        self.prices_tomorrow: list = []
        self.state: float = 0
        self.nordpool_entity: str = ""
        self.average_data: list = []
        if is_active:
            self._setup_nordpool()

    async def update_nordpool(self):
        ret = self._hass.states.get(self.nordpool_entity)
        if ret is not None:
            try:
                ret_attr = list(ret.attributes.get("today"))
                self.prices = ret_attr
            except Exception as e:
                _LOGGER.exception(f"Could not parse today's prices from Nordpool. Unsolveable error. {e}")
                return
            try:
                ret_attr_tomorrow = list(ret.attributes.get("tomorrow"))
                self.prices_tomorrow = ret_attr_tomorrow
            except Exception as e:
                _LOGGER.warning(f"Couldn't parse tomorrow's prices from Nordpool. Array will be empty. {e}")
                self.prices_tomorrow = []
            ret_attr_currency = str(ret.attributes.get("currency"))
            self.currency = ret_attr_currency
            self.state = ret.state
            self._hub.hours.prices = self.prices
            self._hub.hours.prices_tomorrow = self.prices_tomorrow
            try:
                _avg_data = str(ret.attributes.get("average"))
                self.add_average_data(float(_avg_data))
            except Exception as ee:
                _LOGGER.warning(f"Could not parse today's average from Nordpool. {ee}")
        elif self._hub.is_initialized:
            _LOGGER.error("Could not get nordpool-prices")

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
            _LOGGER.error(f"Peaqev was unable to get a Nordpool-entity. Disabling Priceawareness until reboot of HA: {e}")

    def import_average_data(self, incoming: list):
        if isinstance(incoming, list):
            if len(incoming) > 0:
                self.average_data = incoming
        self._cap_average_data_length()

    def add_average_data(self, new_val):
        if isinstance(new_val, float):
            if len(self.average_data) == 0:
                self.average_data.append(new_val)
            elif self.average_data[-1] != new_val:
                self.average_data.append(new_val)
            self._cap_average_data_length()

    def _cap_average_data_length(self):
        while len(self.average_data) > AVERAGE_MAX_LEN:
            del self.average_data[0]

    def get_average(self, days: int) -> float:
        if len(self.average_data) > days:
            ret = self.average_data[-days]
        elif len(self.average_data) == 0:
            return 0.0
        else:
            ret = self.average_data
        return round(mean(ret), 2)
