import logging

from peaqevcore.models.chargerstates import CHARGERSTATES

from custom_components.peaqev.peaqservice.chargecontroller.chargecontrollerbase import ChargeControllerBase

_LOGGER = logging.getLogger(__name__)

class ChargeControllerLite(ChargeControllerBase):
    def __init__(self, hub):
        super().__init__(hub)

    def _get_status_charging(self) -> CHARGERSTATES:
        if self._hub.totalhourlyenergy.value >= self._hub.current_peak_dynamic and self._hub.locale.data.free_charge(self._hub.locale.data) is False:
            ret = CHARGERSTATES.Stop
        else:
            ret = CHARGERSTATES.Start
        return ret

    def _get_status_connected(self, charger_state) -> CHARGERSTATES:
        if self._hub.carpowersensor.value < 1 and self._is_done(charger_state):
            ret = CHARGERSTATES.Done
        else:
            if (self._hub.totalhourlyenergy.value < self._hub.current_peak_dynamic) or self._hub.locale.data.free_charge(self._hub.locale.data) is True:
                ret = CHARGERSTATES.Start
            else:
                ret = CHARGERSTATES.Stop
        return ret
