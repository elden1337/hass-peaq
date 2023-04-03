import logging

from peaqevcore.models.locale.enums.time_periods import TimePeriods

CONSUMPTION = "consumption"
COST = "cost"

_LOGGER = logging.getLogger(__name__)


class GainLoss:
    def __init__(self, hub):
        self._daily_average: float = None
        self._monthly_average: float = None
        self._hub = hub
        self._hub.observer.add("monthly average price changed", self._update_monthly_average)
        self._hub.observer.add("daily average price changed", self._update_daily_average)

    async def state(self, time_period: TimePeriods) -> float:
        ret = 0
        consumption = self._hub.state_machine.states.get(await self._get_entity(time_period, CONSUMPTION))
        cost = self._hub.state_machine.states.get(await self._get_entity(time_period, COST))
        if consumption is not None and cost is not None:
            if any([
                consumption.state == "unknown",
                consumption.state == "unavailable",
                cost.state == "unknown",
                cost.state == "unavailable"
            ]):
                return ret
            average = await self._get_average(time_period)
            cost_divided = float(cost.state)
            consumptionf = float(consumption.state)
            if consumptionf > 0 and cost_divided > 0 and average is not None:
                net = cost_divided / consumptionf
                ret = round((net / average) - 1, 4)
        return ret

    def _update_monthly_average(self, val):
        if isinstance(val, float):
            self._monthly_average = val

    def _update_daily_average(self, val):
        if isinstance(val, float):
            self._daily_average = val

    def _get_monthly_average(self) -> float:
        return self._monthly_average

    def _get_daily_average(self) -> float:
        return self._daily_average

    async def _get_average(self, time_period: TimePeriods) -> float:
        if time_period == TimePeriods.Monthly:
            return self._monthly_average
        if time_period == TimePeriods.Daily:
            return self._daily_average

    @staticmethod
    async def _get_entity(time_period: TimePeriods, resulttype: str):
        ret = {
            TimePeriods.Daily:   {
                CONSUMPTION: "sensor.peaqev_energy_including_car_daily",
                COST:        "sensor.peaqev_energy_cost_integral_daily"
            },
            TimePeriods.Monthly: {
                CONSUMPTION: "sensor.peaqev_energy_including_car_monthly",
                COST:        "sensor.peaqev_energy_cost_integral_monthly"
            }
        }
        return ret.get(time_period).get(resulttype)
