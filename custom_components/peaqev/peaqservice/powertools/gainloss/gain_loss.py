import logging

from peaqevcore.models.locale.enums.time_periods import TimePeriods

from custom_components.peaqev.peaqservice.powertools.gainloss.const import *

_LOGGER = logging.getLogger(__name__)


class GainLoss:
    def __init__(self, hub):
        self._daily_average: float = None
        self._monthly_average: float = None
        self._hub = hub
        self._hub.observer.add(
            "monthly average price changed", self._update_monthly_average
        )
        self._hub.observer.add(
            "daily average price changed", self._update_daily_average
        )

    async def async_state(self, time_period: TimePeriods) -> float:
        consumption = self._hub.state_machine.states.get(
            await self.async_get_entity(time_period, CONSUMPTION)
        )
        cost = self._hub.state_machine.states.get(
            await self.async_get_entity(time_period, COST)
        )
        return await self.async_calculate_state(consumption, cost, time_period)

    async def async_calculate_state(
        self, consumption, cost, time_period: TimePeriods
    ) -> float:
        if consumption is not None and cost is not None:
            if await self.async_check_invalid_states(consumption, cost):
                return 0
            average = await self.async_get_average(time_period)
            if (
                float(consumption.state) > 0
                and float(cost.state) > 0
                and average is not None
            ):
                net = float(cost.state) / float(consumption.state)
                return round((net / average) - 1, 4)
        return 0

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

    @staticmethod
    async def async_check_invalid_states(consumption, cost) -> bool:
        return any(
            [
                str(consumption.state).lower() in INVALID_STATES,
                str(cost.state).lower() in INVALID_STATES,
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
