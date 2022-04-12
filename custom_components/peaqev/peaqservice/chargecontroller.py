from datetime import datetime
import time
import logging
from custom_components.peaqev.peaqservice.util.chargerstates import CHARGECONTROLLER
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)

DONETIMEOUT = 180

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

    def update_latestchargerstart(self):
        self.latestchargerstart = time.time()

    def _let_charge(self):
        chargerstate = self._hub.chargerobject.value.lower()

        if chargerstate in self._hub.chargertypedata.charger.chargerstates[CHARGECONTROLLER.Idle]:
            self.update_latestchargerstart()
            return CHARGECONTROLLER.Idle
        elif chargerstate in self._hub.chargertypedata.charger.chargerstates[CHARGECONTROLLER.Connected] and self._hub.charger_enabled.value is False:
            self.update_latestchargerstart()
            return CHARGECONTROLLER.Connected
        elif chargerstate not in self._hub.chargertypedata.charger.chargerstates[CHARGECONTROLLER.Idle] and self._hub.charger_done.value is True:
            return CHARGECONTROLLER.Done
        elif datetime.now().hour in self._hub.nonhours:
            self.update_latestchargerstart()
            return CHARGECONTROLLER.Stop
        elif chargerstate in self._hub.chargertypedata.charger.chargerstates[CHARGECONTROLLER.Connected]:
            if self._hub.carpowersensor.value < 1 and time.time() - self.latestchargerstart > DONETIMEOUT:
                return CHARGECONTROLLER.Done
            else:
                self.update_latestchargerstart()
                if self.below_startthreshold and self._hub.totalhourlyenergy.value > 0:
                    return CHARGECONTROLLER.Start
                else:
                    return CHARGECONTROLLER.Stop
        elif chargerstate in self._hub.chargertypedata.charger.chargerstates[CHARGECONTROLLER.Charging]:
            self.update_latestchargerstart()
            if self.above_stopthreshold and self._hub.totalhourlyenergy.value > 0:
                return CHARGECONTROLLER.Stop
            else:

                return CHARGECONTROLLER.Start
        else:
            return CHARGECONTROLLER.Error

    # # Implement Python Switch Case Statement using Dictionary
    # def monday(self):
    #     return "monday"
    #
    # def tuesday(self):
    #     return "tuesday"
    #
    # def wednesday(self):
    #     return "wednesday"
    #
    # def thursday(self):
    #     return "thursday"
    #
    # def friday(self):
    #     return "friday"
    #
    # def saturday(self):
    #     return "saturday"
    #
    # def sunday(self):
    #     return "sunday"
    #
    # def default(self):
    #     return "Incorrect day"
    #
    # switcher = {
    #     1: monday,
    #     2: tuesday,
    #     3: wednesday,
    #     4: thursday,
    #     5: friday,
    #     6: saturday,
    #     7: sunday
    # }
    #
    # def switch(self, dayOfWeek):
    #     return self.switcher.get(dayOfWeek, self.default)()
    #
    # print(switch(3))
    # print(switch(5))
