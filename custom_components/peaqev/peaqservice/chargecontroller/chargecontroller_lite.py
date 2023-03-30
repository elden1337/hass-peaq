import logging

from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_helpers import async_defer_start
from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import IChargeController
from custom_components.peaqev.peaqservice.chargecontroller.const import INITIALIZING
_LOGGER = logging.getLogger(__name__)


class ChargeControllerLite(IChargeController):
    def __init__(self, hub, charger_states):
        super().__init__(hub, charger_states)

    @property
    def status_string(self) -> str:
        if not self.is_initialized:
            return INITIALIZING
        return self.status_type.name

    async def async_get_status_charging(self) -> ChargeControllerStates:
        if self.hub.sensors.totalhourlyenergy.value >= self.hub.current_peak_dynamic and not self.hub.is_free_charge:
            ret = ChargeControllerStates.Stop
        else:
            ret = ChargeControllerStates.Start
        return ret

    async def async_get_status_connected(self, charger_state = None) -> ChargeControllerStates:
        if charger_state is not None and self.hub.sensors.carpowersensor.value < 1 and await self.async_is_done(charger_state):
            ret = ChargeControllerStates.Done
        else:
            if (self.hub.totalhourlyenergy.value < self.hub.current_peak_dynamic) or self.hub.is_free_charge:
                ret = ChargeControllerStates.Start if not await async_defer_start(self.hub.hours.non_hours) else ChargeControllerStates.Stop
            else:
                ret = ChargeControllerStates.Stop
        return ret
