from datetime import datetime
from threading import Thread
import custom_components.peaq.peaq.constants as constants
import logging

_LOGGER = logging.getLogger(__name__)

class ChargeController():
    def __init__(self, hub, _status = constants.CHARGECONTROLLER.Idle):
        self._hub = hub
        self.Name = "ChargeController"
        self.status = _status
    
    @property
    def LessThanStartThreshold(self) -> bool: 
        return (self._hub.Prediction.PredictedEnergyThisHour * 1000) < ((self._hub.currentPeak*1000) * (self._hub.Threshold.Start/100))
        
    @property
    def MoreThanStopThreshold(self) -> bool: 
        return (self._hub.Prediction.PredictedEnergyThisHour * 1000) > ((self._hub.currentPeak*1000) * (self._hub.Threshold.Stop/100))
    
    # @property
    # def TotalEnergyThisHourIsNotZero(self) -> bool:
    #     _LOGGER.error("totalenergythis hour: ", self._hub.TotalEnergyThisHour) 
    #     return self._hub.TotalEnergyThisHour > 0

    @property
    def status(self):
        return self.Charge(self._hub)

    @status.setter
    def status(self, value):
        self._status = self.Charge(self._hub)

    def Charge(self, hub) -> str:
            self._hub = hub    
            if self._hub.ChargerEntity.lower() == "available":
                return constants.CHARGECONTROLLER.Idle
            elif self._hub.ChargerEntity.lower() != "available" and self._hub.charging_done == True:
                return constants.CHARGECONTROLLER.Done
            elif datetime.now().hour in self._hub.NonHours:
                return constants.CHARGECONTROLLER.Stop
            elif self._hub.ChargerEntity.lower() == "connected":
                if self.LessThanStartThreshold and self._hub.TotalEnergyThisHour > 0:
                    return constants.CHARGECONTROLLER.Start
                else:
                    return constants.CHARGECONTROLLER.Stop
            elif self._hub.ChargerEntity.lower() == "charging":
                #condition1 = self._hub.carpowersensor < 1 and self._hub.car_energy_hourly > 0
                condition1 = False
                condition2 = self.MoreThanStopThreshold and self._hub.TotalEnergyThisHour > 0
                if condition1 and not condition2:
                    return constants.CHARGECONTROLLER.Done
                elif condition2:
                    return constants.CHARGECONTROLLER.Stop
                else:
                    return constants.CHARGECONTROLLER.Start
            else:
                return constants.CHARGECONTROLLER.Error
