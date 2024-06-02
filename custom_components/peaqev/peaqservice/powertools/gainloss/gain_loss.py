import logging

from peaqevcore.common.models.observer_types import ObserverTypes
from peaqevcore.models.locale.enums.time_periods import TimePeriods

from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.powertools.gainloss.const import *
from custom_components.peaqev.peaqservice.powertools.gainloss.igain_loss import \
    IGainLoss
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade

_LOGGER = logging.getLogger(__name__)


class GainLoss(IGainLoss):
    def __init__(self, observer: IObserver, state_machine: IHomeAssistantFacade):
        super().__init__()
        self.observer = observer
        self.state_machine = state_machine
        self.observer.add(ObserverTypes.MonthlyAveragePriceChanged, self._update_monthly_average)
        self.observer.add(ObserverTypes.DailyAveragePriceChanged, self._update_daily_average)

    async def async_get_consumption(self, time_period: TimePeriods) -> float:
        try:
            consumption = self.state_machine.get_state(
                await self.async_get_entity(time_period, CONSUMPTION)
            )
            return float(consumption.state)
        except AttributeError:
            return 0.0

    async def async_get_cost(self, time_period: TimePeriods) -> float:
        try:
            cost = self.state_machine.get_state(await self.async_get_entity(time_period, COST))
            return float(cost.state)
        except AttributeError:
            return 0.0
