import logging

from peaqevcore.common.models.observer_types import ObserverTypes
from peaqevcore.models.locale.enums.time_periods import TimePeriods

from custom_components.peaqev.peaqservice.powertools.gainloss.const import *
from custom_components.peaqev.peaqservice.powertools.gainloss.igain_loss import \
    IGainLoss

_LOGGER = logging.getLogger(__name__)


class GainLoss(IGainLoss):
    def __init__(self, hub):
        super().__init__()
        self._hub = hub
        self._hub.observer.add(ObserverTypes.MonthlyAveragePriceChanged, self._update_monthly_average)
        self._hub.observer.add(ObserverTypes.DailyAveragePriceChanged, self._update_daily_average)

    async def async_get_consumption(self, time_period: TimePeriods) -> float:
        try:
            consumption = self._hub.state_machine.states.get(
                await self.async_get_entity(time_period, CONSUMPTION)
            )
            return float(consumption.state)
        except AttributeError:
            return 0.0

    async def async_get_cost(self, time_period: TimePeriods) -> float:
        try:
            cost = self._hub.state_machine.states.get(await self.async_get_entity(time_period, COST))
            return float(cost.state)
        except AttributeError:
            return 0.0

