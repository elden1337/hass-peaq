import logging
import time
from datetime import datetime
from peaqevcore.Chargecontroller import ChargeControllerBase as _core
from peaqevcore.Models import CHARGERSTATES
from custom_components.peaqev.peaqservice.chargecontroller.chargecontrollerbase import ChargeControllerBase

_LOGGER = logging.getLogger(__name__)

class ChargeControllerLite(ChargeControllerBase):
    def __init__(self, hub):
        super().__init__(hub)

    def _get_status(self):
        pass
        # ret = CHARGERSTATES.Error
        # update_timer = False
        # charger_state = self._hub.chargerobject.value.lower()
        # free_charge = self._hub.locale.data.free_charge
        #
        # if charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Done]:
        #     self._hub.charger_done.value = True
        #     ret = CHARGERSTATES.Done
        # elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Idle]:
        #     update_timer = True
        #     ret = CHARGERSTATES.Idle
        #     if self._hub.charger_done.value is True:
        #         self._hub.charger_done.value = False
        # elif charger_state in self._hub.chargertype.charger.chargerstates[
        #     CHARGERSTATES.Connected] and self._hub.charger_enabled.value is False:
        #     update_timer = True
        #     ret = CHARGERSTATES.Connected
        # elif charger_state not in self._hub.chargertype.charger.chargerstates[
        #     CHARGERSTATES.Idle] and self._hub.charger_done.value is True:
        #     ret = CHARGERSTATES.Done
        # elif datetime.now().hour in self._hub.hours.non_hours and free_charge is False:
        #     update_timer = True
        #     ret = CHARGERSTATES.Stop
        # elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Connected]:
        #     if self._hub.carpowersensor.value < 1 and time.time() - self.latest_charger_start > DONETIMEOUT:
        #         ret = CHARGERSTATES.Done
        #     else:
        #         if (self.below_startthreshold and self._hub.totalhourlyenergy.value > 0) or free_charge is True:
        #             ret = CHARGERSTATES.Start
        #         else:
        #             update_timer = True
        #             ret = CHARGERSTATES.Stop
        # elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Charging]:
        #     update_timer = True
        #     if self.above_stopthreshold and self._hub.totalhourlyenergy.value > 0 and free_charge is False:
        #         ret = CHARGERSTATES.Stop
        #     else:
        #         ret = CHARGERSTATES.Start
        #
        # if update_timer is True:
        #     self.update_latestchargerstart()
        # return ret

