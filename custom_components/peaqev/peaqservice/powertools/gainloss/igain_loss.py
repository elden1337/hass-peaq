import logging
from abc import abstractmethod

from peaqevcore.models.locale.enums.time_periods import TimePeriods

from custom_components.peaqev.peaqservice.powertools.gainloss.const import *

_LOGGER = logging.getLogger(__name__)


class IGainLoss:
    def __init__(self):
        self._daily_average: float|None = None
        self._monthly_average: float|None = None

    @property
    def is_initialized(self) -> bool:
        return self._daily_average is not None and self._monthly_average is not None

    async def async_state(self, time_period: TimePeriods) -> float:
        if not self.is_initialized:
            return 0.0
        consumption = await self.async_get_consumption(time_period)
        cost = await self.async_get_cost(time_period)
        try:
            return await self.async_calculate_state(consumption, cost, time_period)
        except AttributeError:
            return 0.0

    @abstractmethod
    async def async_get_consumption(self, time_period: TimePeriods) -> float:
        pass

    @abstractmethod
    async def async_get_cost(self, time_period: TimePeriods) -> float:
        pass

    async def async_calculate_state(self, consumption, cost, time_period: TimePeriods) -> float:
        average: float|None = None
        if consumption is not None and cost is not None:
            if await self.async_check_invalid_states(consumption, cost):
                return 0.0
            try:
                average, cost = self.normalize_numbers(await self.async_get_average(time_period), float(cost))
            except TypeError:
                return 0.0
            if float(consumption) > 0 and cost > 0 and average is not None:
                net = cost / float(consumption)
                try:
                    ret = round((net / average) - 1, 4)
                    return max(-1.0,min(ret,1.0))
                except ZeroDivisionError:
                    return 0.0
        return 0.0

    @staticmethod
    def normalize_numbers(average:float, cost:float):
        try:
            if min(average, cost) < 0:
                diff = abs(min(average, cost)) + 0.01
                average += diff
                cost += diff
            return round(average, 3), round(cost, 3)
        except TypeError as T:
            _LOGGER.warning(f"normalize_numbers. Can't calculate gain/loss: {T}. avg: {average}, cost: {cost}")
            return average, cost

    def _update_monthly_average(self, val):
        if isinstance(val, float):
            self._monthly_average = val

    def _update_daily_average(self, val):
        if isinstance(val, float):
            self._daily_average = val

    async def async_get_average(self, time_period: TimePeriods) -> float:
        if time_period == TimePeriods.Monthly:
            return self._monthly_average
        if time_period == TimePeriods.Daily:
            return self._daily_average
        raise ValueError(f"Invalid time period: {time_period}")

    @staticmethod
    async def async_check_invalid_states(consumption, cost) -> bool:
        return any(
            [
                str(consumption).lower() in INVALID_STATES,
                str(cost).lower() in INVALID_STATES,
            ]
        )

    @staticmethod
    async def async_get_entity(time_period: TimePeriods, resulttype: str):
        ret = {
            TimePeriods.Daily: {
                CONSUMPTION: DAILY_ENERGY_SENSOR,
                COST: DAILY_COST_SENSOR,
            },
            TimePeriods.Monthly: {
                CONSUMPTION: MONTHLY_ENERGY_SENSOR,
                COST: MONTHLY_COST_SENSOR,
            },
        }
        return ret.get(time_period).get(resulttype)
