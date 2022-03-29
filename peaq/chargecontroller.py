from datetime import datetime
from threading import Thread
import custom_components.peaq.peaq.constants as constants
import logging

_LOGGER = logging.getLogger(__name__)

class ChargeController():
    def __init__(self, hub, inputstatus = constants.CHARGECONTROLLER.Idle):
        self._hub = hub
        self.Name = "ChargeController"
        self._status = inputstatus
    
    @property
    def LessThanStartThreshold(self) -> bool: 
        return (self._hub.prediction.predictedenergy * 1000) < ((self._hub.currentpeak.value*1000) * (self._hub.threshold.start/100))
        
    @property
    def MoreThanStopThreshold(self) -> bool: 
        return (self._hub.prediction.predictedenergy * 1000) > ((self._hub.currentpeak.value*1000) * (self._hub.threshold.stop/100))

    @property
    def status(self):
        return self.Charge(self._hub)

    @status.setter
    def status(self, value):
        self._status = self.Charge(self._hub)

    def Charge(self, hub) -> str:
            self._hub = hub    
            if self._hub.chargerobject.value.lower() == "available":
                return constants.CHARGECONTROLLER.Idle
            elif self._hub.chargerobject.value.lower() != "available" and self._hub.charger_done.value == True:
                return constants.CHARGECONTROLLER.Done
            elif datetime.now().hour in self._hub.nonhours:
                return constants.CHARGECONTROLLER.Stop
            elif self._hub.chargerobject.value.lower() == "connected":
                if self.LessThanStartThreshold and self._hub.totalhourlyenergy.value > 0:
                    return constants.CHARGECONTROLLER.Start
                else:
                    return constants.CHARGECONTROLLER.Stop
            elif self._hub.chargerobject.value.lower() == "charging":
                #condition1 = self._hub.carpowersensor.value < 1 and self._hub.car_energy_hourly > 0
                condition1 = False
                condition2 = self.MoreThanStopThreshold and self._hub.totalhourlyenergy.value > 0
                if condition1 and not condition2:
                    return constants.CHARGECONTROLLER.Done
                elif condition2:
                    return constants.CHARGECONTROLLER.Stop
                else:
                    return constants.CHARGECONTROLLER.Start
            else:
                return constants.CHARGECONTROLLER.Error
