from abc import abstractmethod
from datetime import datetime
import logging
from custom_components.peaqev.peaqservice.util.constants import (
    NON_HOUR,
    CAUTION_HOUR,
    CHARGING_PERMITTED,
    CAUTIONHOURTYPE_INTERMEDIATE,
    CAUTIONHOURTYPE_DICT
)

import homeassistant.helpers.template as template
from peaqevcore.hoursselection import Hoursselectionbase as core_hours

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
        elif datetime.now().hour in self.caution_hours:
            return CAUTION_HOUR
        else:
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

class RegularHours(Hours):
    def __init__(self, non_hours=None, caution_hours=None):
        super().__init__(False, non_hours, caution_hours)


class PriceAwareHours(Hours):
    def __init__(
            self,
            hass,
            price_aware: bool,
            absolute_top_price: float = None,
            non_hours: list = None,
            caution_hours: list = None,
            cautionhour_type: str = CAUTIONHOURTYPE_INTERMEDIATE
    ):
        self._absolute_top_price = self._set_absolute_top_price(absolute_top_price)
        self._cautionhour_type = CAUTIONHOURTYPE_DICT[cautionhour_type]
        self._cautionhour_type_string = cautionhour_type
        self._core = core_hours(self._absolute_top_price, self._cautionhour_type)
        self._hass = hass
        self._prices = []
        self._nordpool_entity = None
        self._setup_nordpool()
        super().__init__(price_aware, non_hours, caution_hours)

    @property
    def cautionhour_type_string(self) -> str:
        return self._cautionhour_type_string

    @Hours.non_hours.getter
    def non_hours(self) -> list:
        return self._core.non_hours

    @Hours.caution_hours.getter
    def caution_hours(self) -> list:
        return self._core.caution_hours

    @property
    def absolute_top_price(self):
        return self._absolute_top_price

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

    def update_nordpool(self):
        ret = self._hass.states.get(self.nordpool_entity)
        if ret is not None:
            ret_attr = list(ret.attributes.get("today"))
            ret_attr_tomorrow = list(ret.attributes.get("tomorrow"))
            self.prices = ret_attr
            self.prices_tomorrow = ret_attr_tomorrow
        else:
            _LOGGER.warn("could not get nordpool-prices")

    def _setup_nordpool(self):
        try:
            entities = template.integration_entities(self._hass, NORDPOOL)
            if len(entities) < 1:
                raise Exception("no entities found for Nordpool.")
            elif len(entities) == 1:
                self.nordpool_entity = entities[0]
                self.update_nordpool()
            else:
                raise Exception("more than one Nordpool entity found. Cannot continue.")
        except Exception:
            _LOGGER.warn("Peaqev was unable to get a Nordpool-entity. Disabling Priceawareness.")

    @staticmethod
    def _set_absolute_top_price(_input) -> float:
        if _input is None or _input <= 0:
            return float("inf")
        return _input



