import logging
import time

from peaqevcore.Models import CHARGERSTATES

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

    def _get_status_connected(self) -> CHARGERSTATES:
        if self._hub.carpowersensor.value < 1 and time.time() - self.latest_charger_start > self.DONETIMEOUT:
            ret = CHARGERSTATES.Done
        else:
            if (self._hub.totalhourlyenergy.value < self._hub.current_peak_dynamic) or self._hub.locale.data.free_charge(self._hub.locale.data) is True:
                ret = CHARGERSTATES.Start
            else:
                ret = CHARGERSTATES.Stop
        return ret
