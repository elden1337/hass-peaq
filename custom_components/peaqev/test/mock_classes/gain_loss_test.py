from peaqevcore.models.locale.enums.time_periods import TimePeriods

from custom_components.peaqev.peaqservice.powertools.gainloss.const import *
from custom_components.peaqev.peaqservice.powertools.gainloss.igain_loss import \
    IGainLoss


class GainLossTest(IGainLoss):
    def __init__(self, mock_states = None):
        self._mock_states = mock_states
        super().__init__()

    async def async_get_consumption(self, time_period: TimePeriods) -> float:
        try:
            consumption = self._mock_states.get(
                await self.async_get_entity(time_period, CONSUMPTION)
            )
            return float(consumption)
        except AttributeError:
            return 0.0

    async def async_get_cost(self, time_period: TimePeriods) -> float:
        try:
            cost = self._mock_states.get(await self.async_get_entity(time_period, COST))
            return float(cost)
        except AttributeError:
            return 0.0