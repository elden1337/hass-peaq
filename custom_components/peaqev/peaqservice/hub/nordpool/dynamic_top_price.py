from datetime import datetime
from statistics import mean
import logging
from typing import Tuple
from custom_components.peaqev.peaqservice.hub.nordpool.average_type import AverageType

_LOGGER = logging.getLogger(__name__)


class DynamicTopPrice:
    def __init__(self):
        self._three = []
        self._seven = []
        self._month = []
        self.filterlen = {AverageType.SEVEN: 14, AverageType.THREE: 6}

    async def async_get_max(self, prices: list) -> Tuple[float, AverageType]:
        if not len(prices):
            _LOGGER.warning("No prices to calculate max from.")
            return 0, AverageType.ERROR
        await self.async_set_lists(prices)
        a = self._month[-1]
        b = self._three[-1]
        c = self._seven[-1]
        rets = {a: AverageType.MONTH}
        rets.update(await self.async_measure_type(a, b, AverageType.THREE))
        rets.update(await self.async_measure_type(a, c, AverageType.SEVEN))
        return round(max(rets.keys()), 2), rets[max(rets.keys())]

    async def async_set_lists(self, prices: list) -> None:
        self._three = await self.async_get_rolling(prices, 3)
        self._seven = await self.async_get_rolling(prices, 7)
        self._month = await self.async_get_current_month(prices)

    async def async_measure_type(self, month, measure, avg_type: AverageType) -> dict:
        ret = {}
        if measure > month and datetime.now().day >= self.filterlen[avg_type]:
            gr = await self.async_set_gradient(self._seven)
            if gr[-1] > 0:
                ret = {mean([month, measure]): avg_type}
        return ret

    @staticmethod
    async def async_get_rolling(prices: list = [], days: int = 1):
        """get rolling seven day average from prices for each day."""
        rolling = []
        if not len(prices):
            return []
        listlen = len(prices)
        for i in range((listlen - datetime.now().day), listlen):
            rolling.append(mean(prices[i - days : i]))
        return rolling

    @staticmethod
    async def async_get_current_month(prices: list = []):
        rolling = []
        if not len(prices):
            print("bad")
            return []
        listlen = len(prices)
        start_at = listlen - datetime.now().day
        for i in range(start_at, listlen):
            rolling.append(mean(prices[start_at : i + 1]))
        return rolling

    @staticmethod
    async def async_set_gradient(averages: list):
        """calculate the gradient of a list."""
        gradient = [0]
        for i in range(1, len(averages)):
            gradient.append(averages[i] - averages[i - 1])
        return gradient


# import asyncio
# prfices = [0.74, 1.14, 1.04, 0.65, 0.52, 0.6, 0.43, 0.73, 0.9, 1.12, 1.48, 1.03, 0.82, 0.63, 0.77, 0.78, 1.49, 1.67, 1.58, 1.36, 0.85, 0.82, 0.79, 0.47, 0.49, 0.61, 0.31, 0.52, 0.64, 1.08, 1.48, 1.26]
# async def run():
#     h = DynamicTopPrice()
#     h.prices = prfices
#     gg = await h.async_get_max()
#     print(gg)

# asyncio.run(run())
