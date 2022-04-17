from datetime import datetime
import time
import logging
from typing import Tuple

from custom_components.peaqev.peaqservice.util.chargerstates import CHARGECONTROLLER
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)

DONETIMEOUT = 180


class ChargeController:
    def __init__(self, hub):
        self._hub = hub
        self.name = f"{self._hub.hubname} {CHARGERCONTROLLER}"
        self._status = CHARGECONTROLLER.Idle
        self._latestchargerstart = time.time()

    @property
    def latest_charger_start(self):
        return self._latestchargerstart

    @latest_charger_start.setter
    def latest_charger_start(self, val):
        self._latestchargerstart = val

    @property
    def below_startthreshold(self) -> bool:
        return (self._hub.prediction.predictedenergy * 1000) < (
                (self._hub.currentpeak.value * 1000) * (self._hub.threshold.start / 100))

    @property
    def above_stopthreshold(self) -> bool:
        return (self._hub.prediction.predictedenergy * 1000) > (
                (self._hub.currentpeak.value * 1000) * (self._hub.threshold.stop / 100))

    @property
    def status(self):
        return self._let_charge()

    def update_latestchargerstart(self):
        self.latest_charger_start = time.time()

    def _let_charge(self):
        charger_state = self._hub.chargerobject.value.lower()
        ret = CHARGECONTROLLER.Error
        update_timer = False

        if charger_state in self._hub.chargertype.charger.chargerstates[CHARGECONTROLLER.Idle]:
            update_timer = True
            ret = CHARGECONTROLLER.Idle
        elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGECONTROLLER.Connected] and self._hub.charger_enabled.value is False:
            update_timer = True
            ret = CHARGECONTROLLER.Connected
        elif charger_state not in self._hub.chargertype.charger.chargerstates[CHARGECONTROLLER.Idle] and self._hub.charger_done.value is True:
            ret = CHARGECONTROLLER.Done
        elif datetime.now().hour in self._hub.nonhours:
            update_timer = True
            ret = CHARGECONTROLLER.Stop
        elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGECONTROLLER.Connected]:
            if self._hub.carpowersensor.value < 1 and time.time() - self.latest_charger_start > DONETIMEOUT:
                ret = CHARGECONTROLLER.Done
            else:
                if self.below_startthreshold and self._hub.totalhourlyenergy.value > 0:
                    ret = CHARGECONTROLLER.Start
                else:
                    update_timer = True
                    ret = CHARGECONTROLLER.Stop
        elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGECONTROLLER.Charging]:
            update_timer = True
            if self.above_stopthreshold and self._hub.totalhourlyenergy.value > 0:
                ret = CHARGECONTROLLER.Stop
            else:
                ret = CHARGECONTROLLER.Start

        if update_timer is True:
            self.update_latestchargerstart()
        return ret
