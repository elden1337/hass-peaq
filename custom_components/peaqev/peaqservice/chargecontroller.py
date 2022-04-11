from datetime import datetime
import time
import logging
from custom_components.peaqev.peaqservice.util.chargerstates import CHARGECONTROLLER
from custom_components.peaqev.peaqservice.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)


class ChargeController():
    def __init__(self, hub):
        self._hub = hub
        self.name = f"{self._hub.hubname} {CHARGERCONTROLLER}"
        self._status = CHARGECONTROLLER.Idle
        self._latestchargerstart = time.time()

    @property
    def latestchargerstart(self):
        return self._latestchargerstart

    @latestchargerstart.setter
    def latestchargerstart(self, val):
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

    def _let_charge(self):
        chargerstate = self._hub.chargerobject.value.lower()

        if chargerstate in self._hub.chargertypedata.charger.chargerstates[CHARGECONTROLLER.Idle]:
            return CHARGECONTROLLER.Idle
        elif chargerstate in self._hub.chargertypedata.charger.chargerstates[CHARGECONTROLLER.Connected] and self._hub.charger_enabled.value is False:
            return CHARGECONTROLLER.Connected
        elif chargerstate not in self._hub.chargertypedata.charger.chargerstates[CHARGECONTROLLER.Idle] and self._hub.charger_done.value is True:
            return CHARGECONTROLLER.Done
        elif datetime.now().hour in self._hub.nonhours:
            return CHARGECONTROLLER.Stop
        elif chargerstate in self._hub.chargertypedata.charger.chargerstates[CHARGECONTROLLER.Connected]:
            if self._hub.carpowersensor.value < 1 and time.time() - self.latestchargerstart > 120:
                return CHARGECONTROLLER.Done
            elif self.below_startthreshold and self._hub.totalhourlyenergy.value > 0:
                return CHARGECONTROLLER.Start
            else:
                return CHARGECONTROLLER.Stop
        elif chargerstate in self._hub.chargertypedata.charger.chargerstates[CHARGECONTROLLER.Charging]:
            if self.above_stopthreshold and self._hub.totalhourlyenergy.value > 0:
                return CHARGECONTROLLER.Stop
            else:
                return CHARGECONTROLLER.Start
        else:
            return CHARGECONTROLLER.Error
