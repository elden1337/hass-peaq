import logging

from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import IChargeController

_LOGGER = logging.getLogger(__name__)


class ChargeControllerLite(IChargeController):
    def __init__(self, hub):
        super().__init__(hub)

    def _get_status_charging(self) -> ChargeControllerStates:
        if self._hub.sensors.totalhourlyenergy.value >= self._hub.current_peak_dynamic and self._hub.sensors.locale.data.free_charge(self._hub.sensors.locale.data) is False:
            ret = ChargeControllerStates.Stop
        else:
            ret = ChargeControllerStates.Start
        return ret

    def _get_status_connected(self, charger_state = None) -> ChargeControllerStates:
        if charger_state is not None and self._hub.sensors.carpowersensor.value < 1 and self._is_done(charger_state):
            ret = ChargeControllerStates.Done
        else:
            if (self._hub.totalhourlyenergy.value < self._hub.current_peak_dynamic) or self._hub.locale.data.free_charge(self._hub.locale.data) is True:
                ret = ChargeControllerStates.Start if not self._defer_start(self._hub.hours.non_hours) else ChargeControllerStates.Stop
            else:
                ret = ChargeControllerStates.Stop
        return ret
