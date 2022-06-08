import logging
from abc import abstractmethod
from datetime import datetime

import homeassistant.helpers.template as template
from peaqevcore.hoursselection import Hoursselectionbase as core_hours

from custom_components.peaqev.peaqservice.util.constants import (
    NON_HOUR,
    CAUTION_HOUR,
    CHARGING_PERMITTED,
    CAUTIONHOURTYPE_INTERMEDIATE,
    CAUTIONHOURTYPE_DICT
)

NORDPOOL = "nordpool"
_LOGGER = logging.getLogger(__name__)

"""
This class will return the set nonhours and cautionhours, or generate dynamic ones based on Nordpool
if user has set that bool in config flow.
"""

class Hours():
    def __init__(
            self,
            price_aware: bool,
            non_hours: list = None,
            caution_hours: list = None
    ):
        self._non_hours = non_hours
        self._caution_hours = caution_hours
        self._price_aware = price_aware

    @property
    def state(self) -> str:
        if datetime.now().hour in self.non_hours:
            return NON_HOUR
        if datetime.now().hour in self.caution_hours:
            return CAUTION_HOUR
        return CHARGING_PERMITTED

    @property
    def price_aware(self) -> bool:
        return self._price_aware

    @property
    def non_hours(self):
        return self._non_hours

    @non_hours.setter
    def non_hours(self, val):
        self._non_hours = val

    @property
    def caution_hours(self):
        return self._caution_hours

    @caution_hours.setter
    def caution_hours(self, val):
        self._caution_hours = val

    @property
    @abstractmethod
    def nordpool_entity(self):
        pass

    @abstractmethod
    def update_nordpool(self):
        pass

    @property
    @abstractmethod
    def dynamic_caution_hours(self) -> dict:
        pass

class RegularHours(Hours):
    def __init__(self, non_hours=None, caution_hours=None):
        super().__init__(False, non_hours, caution_hours)

    @property
    def nordpool_entity(self):
        pass

    def update_nordpool(self):
        pass

    @property
    def dynamic_caution_hours(self) -> dict:
        pass

    @property
    def is_initialized(self) -> bool:
        return True


class PriceAwareHours(Hours):
    def __init__(
            self,
            hass,
            hub,
            absolute_top_price: float = None,
            min_price: float = 0,
            cautionhour_type: str = CAUTIONHOURTYPE_INTERMEDIATE
    ):
        self._hub = hub
        self._absolute_top_price = self._set_absolute_top_price(absolute_top_price)
        self._min_price = min_price
        self._cautionhour_type = CAUTIONHOURTYPE_DICT[cautionhour_type]
        self._cautionhour_type_string = cautionhour_type
        self._core = core_hours(self._absolute_top_price, self._min_price, self._cautionhour_type)
        self._hass = hass
        self._prices = []
        self._nordpool_entity = None
        self._nordpool_currency = ""
        self._is_initialized = False
        self._setup_nordpool()
        super().__init__(True)

    @property
    def dynamic_caution_hours(self) -> dict:
        return self._core.dynamic_caution_hours

    @property
    def cautionhour_type_string(self) -> str:
        return self._cautionhour_type_string

    @property
    def non_hours(self) -> list:
        return self._core.non_hours

    @property
    def caution_hours(self) -> list:
        return self._core.caution_hours

    @property
    def absolute_top_price(self):
        return self._absolute_top_price

    @property
    def min_price(self):
        return self._min_price

    @property
    def nordpool_entity(self) -> str:
        return self._nordpool_entity

    @nordpool_entity.setter
    def nordpool_entity(self, val):
        self._nordpool_entity = val

    @property
    def prices(self) -> list:
        return self._core.prices

    @prices.setter
    def prices(self, val):
        self._core.prices = val

    @property
    def prices_tomorrow(self) -> list:
        return self._core.prices_tomorrow

    @prices_tomorrow.setter
    def prices_tomorrow(self, val):
        self._core.prices_tomorrow = val

    @property
    def currency(self):
        return self._nordpool_currency

    @currency.setter
    def currency(self, val):
        self._nordpool_currency = val

    @property
    def is_initialized(self) -> bool:
        if self.prices is not None:
            if len(self.prices) > 0:
                if self._is_initialized is False:
                    self._is_initialized = True
                    _LOGGER.debug("Hourselection has initialized")
                return True
        return False

    def get_average_kwh_price(self):
        if self._is_initialized:
            try:
                return self._core.get_average_kwh_price()
            except ZeroDivisionError as e:
                _LOGGER.warning(e)
        return 0

    def get_total_charge(self):
        if self._is_initialized:
            try:
                return self._core.get_total_charge(self._hub.currentpeak.value)
            except ZeroDivisionError as e:
                _LOGGER.warning(e)
        return 0

    def update_nordpool(self):
        ret = self._hass.states.get(self.nordpool_entity)
        if ret is not None:
            ret_attr = list(ret.attributes.get("today"))
            ret_attr_tomorrow = list(ret.attributes.get("tomorrow"))
            ret_attr_currency = str(ret.attributes.get("currency"))
            self.currency = ret_attr_currency
            self.prices = ret_attr
            self.prices_tomorrow = ret_attr_tomorrow
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

    @staticmethod
    def _set_absolute_top_price(_input) -> float:
        if _input is None or _input <= 0:
            return float("inf")
        return _input
