from datetime import datetime
import time

"""
This class will return the set nonhours and cautionhours, or generate dynamic ones based on Nordpool
if user has set that bool in config flow.
"""


class Hours:
    def __init__(self):
        self._prices = []
        self._nonhours = []
        self._cautionhours = []
        self._last_run = time.time()

    @property
    def nonhours(self):
        return self._nonhours

    @nonhours.setter
    def nonhours(self, val):
        self._nonhours = val

    @property
    def cautionhours(self):
        return self._cautionhours

    @cautionhours.setter
    def cautionhours(self, val):
        self._cautionhours = val

    @property
    def prices(self):
        return self._prices

    @prices.setter
    def prices(self, val):
        self._prices = val
        self._update()

    def _update(self):
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

        self.nonhours = _nh
        self.cautionhours = _ch
