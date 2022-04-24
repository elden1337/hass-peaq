import time
import statistics as stat
import logging

import homeassistant.helpers.template as template


CAUTIONHOURTYPE_SUAVE = "Suave"
CAUTIONHOURTYPE_INTERMEDIATE = "Intermediate"
CAUTIONHOURTYPE_AGGRESSIVE = "Aggressive"

CautionHourType = {
    CAUTIONHOURTYPE_SUAVE: 0.3,
    CAUTIONHOURTYPE_INTERMEDIATE: 0.45,
    CAUTIONHOURTYPE_AGGRESSIVE: 0.6
}

_LOGGER = logging.getLogger(__name__)

"""
This class will return the set nonhours and cautionhours, or generate dynamic ones based on Nordpool
if user has set that bool in config flow.
"""

# https://github.com/custom-components/nordpool

class PriceAwareHours:
    def __init__(
            self,
            hass,
            absolute_top_price: float = None,
            cautionhour_type: float = CautionHourType[CAUTIONHOURTYPE_INTERMEDIATE]
    ):
        self._hass = hass
        self._prices = []
        self._nordpool_entity = None
        self._absolute_top_price = absolute_top_price
        self._cautionhour_type = cautionhour_type
        self._last_run = time.time()
        self._setup_nordpool()
        self.update()

    @property
    def prices(self):
        return self._prices

    @prices.setter
    def prices(self, val):
        self._prices = val
        self.update()

    def update(self):
        self._update_nordpool()
        if len(self.prices) > 1:
            pricedict = self._create_dict(self.prices)
            """
            Curve is too flat if stdev is <= 0.05. 
            If so we don't do any specific non or caution-hours based on pricing.
            """
            if stat.stdev(self.prices) > 0.05:
                self._determine_hours(
                    self._rank_prices(pricedict)
                )

            if self._absolute_top_price is not None:
                self._add_expensive_non_hours(pricedict)

    def _add_expensive_non_hours(self, hourdict: dict):
        lst = (h for h in hourdict if hourdict[h] >= self._absolute_top_price)
        for h in lst:
            if h not in self.non_hours:
                self.non_hours.append(h)
                if h in self.caution_hours:
                    del self.caution_hours[h]
        self.non_hours.sort()

    def _rank_prices(self, hourdict: dict):
        ret = {}
        _maxval = max(hourdict.values())
        for key in hourdict:
            if hourdict[key] > _maxval * (1 - stat.stdev(hourdict.values())):
                ret[key] = {"val": hourdict[key], "permax": round(hourdict[key] / _maxval, 2)}
        return ret

    def _create_dict(self, input: list):
        ret = {}
        for idx, val in enumerate(input):
            ret[idx] = val
        return ret

    def _determine_hours(self, price_list: dict):
        _nh = []
        _ch = {}
        for p in price_list:
            if round(abs(price_list[p]["permax"] - 1), 2) <= self._cautionhour_type:
                _nh.append(p)
            else:
                _ch[p] = round(abs(price_list[p]["permax"] - 1), 2)

        self.non_hours = _nh
        self.caution_hours = _ch

    def _update_nordpool(self):
        ret = self._hass.states.get(self._nordpool_entity)
        if ret is not None:
            ret_attr = str(ret.attributes.get("Today"))
            self.prices = ret_attr
        else:
            _LOGGER.error("chargerobject state was none")

    def _setup_nordpool(self):
        try:
            entities = template.integration_entities(self._hass, "nordpool")
            if len(entities) < 1:
                raise Exception("no entities found for Nordpool.")
            elif len(entities) == 1:
                self._nordpool_entity = entities
            else:
                raise Exception("more than one Nordpool entity found. Cannot continue.")
        except Exception:
            # could not get the entity. supress further priceawareness.
            _LOGGER.warn("Peaqev was unable to get a Nordpool-entity. Disabling Priceawareness.")


class Hours(PriceAwareHours):
    def __init__(
            self,
            hass,
            price_aware: bool,
            absolute_top_price: float = None,
            cautionhour_type: float = None,
            non_hours: list = None,
            caution_hours: dict = None
    ):
        self._non_hours = non_hours
        self._caution_hours = caution_hours
        if price_aware is True:
            super().__init__(hass, absolute_top_price, cautionhour_type)

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


