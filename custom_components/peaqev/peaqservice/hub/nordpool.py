import logging

import homeassistant.helpers.template as template

_LOGGER = logging.getLogger(__name__)

NORDPOOL = "nordpool"

class NordPoolUpdater:
    def __init__(self, hass, hub):
        self._hass = hass
        self._hub = hub
        self.currency: str = ""
        self.prices: list = []
        self.prices_tomorrow: list = []
        self.state:float  = 0
        self.nordpool_entity: str = ""

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
        else:
            _LOGGER.error("could not get nordpool-prices")

    def _setup_nordpool(self):
        try:
            entities = template.integration_entities(self._hass, NORDPOOL)
            if len(entities) < 1:
                raise Exception("no entities found for Nordpool.")
            if len(entities) == 1:
                self.nordpool_entity = entities[0]
                self.update_nordpool()
            else:
                raise Exception("more than one Nordpool entity found. Cannot continue.")
        except Exception as e:
            msg = f"Peaqev was unable to get a Nordpool-entity. Disabling Priceawareness: {e}"
            _LOGGER.error(msg)
