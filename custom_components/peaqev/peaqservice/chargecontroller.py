from datetime import datetime
import logging
import custom_components.peaqev.peaqservice.constants as constants
from custom_components.peaqev.peaqservice.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)


class ChargeController():
    def __init__(self, hub, inputstatus=constants.CHARGECONTROLLER.Idle):
        self._hub = hub
        self.name = f"{self._hub.hubname} {CHARGERCONTROLLER}"
        self._status = inputstatus

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

    def _let_charge(self) -> str:
        if self._hub.chargerobject.value.lower() not in self._hub.chargertypedata.charger.chargerstates["idle"] and self._hub.chargerobject.value.lower() not in self._hub.chargertypedata.charger.chargerstates["connected"] and self._hub.chargerobject.value.lower() not in self._hub.chargertypedata.charger.chargerstates["charging"]:
            _LOGGER.warn("let_charge couldnt process chargerobjectstate", self._hub.chargerobject.value.lower())
            return constants.CHARGECONTROLLER.CheckChargerEntity

        if self._hub.chargerobject.value.lower() in self._hub.chargertypedata.charger.chargerstates["idle"]:
            return constants.CHARGECONTROLLER.Idle
        elif self._hub.chargerobject.value.lower() not in self._hub.chargertypedata.charger.chargerstates["idle"] and self._hub.charger_done.value is True:
            return constants.CHARGECONTROLLER.Done
        elif datetime.now().hour in self._hub.nonhours:
            return constants.CHARGECONTROLLER.Stop
        elif self._hub.chargerobject.value.lower() in self._hub.chargertypedata.charger.chargerstates["connected"]:
            if self.below_startthreshold and self._hub.totalhourlyenergy.value > 0:
                return constants.CHARGECONTROLLER.Start
            else:
                return constants.CHARGECONTROLLER.Stop
        elif self._hub.chargerobject.value.lower() in self._hub.chargertypedata.charger.chargerstates["charging"]:
            # condition1 = self._hub.carpowersensor.value < 1 and self._hub.car_energy_hourly > 0
            condition1 = False
            condition2 = self.above_stopthreshold and self._hub.totalhourlyenergy.value > 0
            if condition1 and not condition2:
                return constants.CHARGECONTROLLER.Done
            elif condition2:
                return constants.CHARGECONTROLLER.Stop
            else:
                return constants.CHARGECONTROLLER.Start
        else:
            _LOGGER.warn("let_charge reported error!", self._hub.chargerobject.value.lower())
            return constants.CHARGECONTROLLER.Error
