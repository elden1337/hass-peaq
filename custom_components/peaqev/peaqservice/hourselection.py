from datetime import datetime
import time

"""
This class will return the set nonhours and cautionhours, or generate dynamic ones based on Nordpool
if user has set that bool in config flow.
"""


class PriceAwareHours:
    def __init__(self):
        self._prices = []
        self._last_run = time.time()
        self._update()

    @property
    def prices(self):
        return self._prices

    @prices.setter
    def prices(self, val):
        self._prices = val
        self._update()

    def _update(self):
        # get new prices from nordpool here
        pricedict = self._create_dict(self.prices)
        rank = self._rank_prices(pricedict)
        self._determine_hours(rank)

    def _rank_prices(self, hourdict: dict):
        ret = {}
        _maxval = max(hourdict.values())

        for key in hourdict:
            if hourdict[key] > _maxval * 0.5:  # only push stuff larger than 50%
                ret[key] = {"val": hourdict[key], "permax": round(hourdict[key] / _maxval, 2)}
        return ret

    def _create_dict(self, input: list):
        ret = {}

        for idx, val in enumerate(input):
            ret[idx] = val
        return ret

    def _determine_hours(self, pricelist: dict):
        _nh = []
        _ch = []
        for p in pricelist:
            if p >= datetime.now().hour:
                if pricelist[p]["permax"] >= 0.75:
                    _nh.append(p)
                else:
                    _ch.append(p)

        self.non_hours = _nh
        self.caution_hours = _ch


class HoursBase:
    def __init__(
            self,
            non_hours: list = None,
            caution_hours: dict = None
    ):
        self._non_hours = non_hours
        self._caution_hours = caution_hours

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



class Hours(PriceAwareHours):
    def __init__(
            self,
            price_aware: bool,
            non_hours: list = None,
            caution_hours: dict = None
    ):
        self._non_hours = non_hours
        self._caution_hours = caution_hours
        if price_aware is True:
            super.__init__(self)

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


