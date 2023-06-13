import logging

from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_helpers import \
    defer_start
from custom_components.peaqev.peaqservice.chargecontroller.const import \
    INITIALIZING
from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import \
    IChargeController

_LOGGER = logging.getLogger(__name__)


class ChargeControllerLite(IChargeController):
    def __init__(self, hub, charger_states, charger_type):
        super().__init__(hub, charger_states, charger_type)

    @property
    def status_string(self) -> str:
        if not self.is_initialized:
            return INITIALIZING
        return self.status_type.name

    async def async_get_status_charging(self) -> ChargeControllerStates:
        if (
            self.hub.sensors.totalhourlyenergy.value >= self.hub.current_peak_dynamic
            and not await self.hub.async_free_charge()
        ):
            ret = ChargeControllerStates.Stop
        else:
            ret = ChargeControllerStates.Start
        return ret

    async def async_get_status_connected(self, charger_state=None) -> ChargeControllerStates:
        if not self.hub.enabled:
            return ChargeControllerStates.Connected
        if (
            charger_state is not None
            and self.hub.sensors.carpowersensor.value < 1
            and await self.async_is_done(charger_state)
        ):
            ret = ChargeControllerStates.Done
        else:
            if (self.hub.totalhourlyenergy.value < self.hub.current_peak_dynamic) or await self.hub.async_free_charge():
                ret = (
                    ChargeControllerStates.Start
                    if not defer_start(self.hub.hours.non_hours)
                    else ChargeControllerStates.Stop
                )
            else:
                ret = ChargeControllerStates.Stop
        return ret
