from datetime import datetime
from threading import Thread
import custom_components.peaq.constants as constants
from custom_components.peaq.prediction import Prediction as p
from custom_components.peaq.threshold import Threshold as th

class ChargeController():
    def __init__(self, hub, _status = constants.CHARGECONTROLLER.Idle):
        self.hub = hub
        self.LessThanStartThreshold
        self.MoreThanStopThreshold
        self.TotalEnergyThisHourIsNotZero
        self.Name = "ChargeController"
        self.status = _status
    
    @property
    def LessThanStartThreshold(self) -> bool: 
        return (p.PredictedEnergyThisHour.__get__(self) * 1000) < (self.hub.currentPeak * (th.Start.__get__(self)/100))
    
    @property
    def MoreThanStopThreshold(self) -> bool: 
        return (p.PredictedEnergyThisHour.__get__(self) * 1000) > (self.hub.currentPeak * (th.Stop.__get__(self)/100))
    
    @property
    def TotalEnergyThisHourIsNotZero(self) -> bool: 
        return self.hub.TotalEnergyThisHour > 0

    @property
    def status(self):
        return self.Charge()

    @status.setter
    def status(self, value):
        self._status = self.Charge()

    #main method, make event out of this that other methods can subscribe to.
    def Charge(self) -> str:
            if self.hub.chargeamps == "Available":
                return constants.CHARGECONTROLLER.Idle
            elif self.hub.chargeamps != "Available" and self.hub.charging_done == True:
                return constants.CHARGECONTROLLER.Done
            elif datetime.now().hour in self.hub.nonhours:
                return constants.CHARGECONTROLLER.Stop
            elif self.hub.chargeamps == "Connected":
                if self.LessThanStartThreshold and self.TotalEnergyThisHourIsNotZero:
                    return constants.CHARGECONTROLLER.Start
                else:
                    return constants.CHARGECONTROLLER.Stop
            elif self.hub.chargeamps == "Charging":
                #condition1 = int(self.hub.chargeampsswitch["current_power"]) < 1 and self.hub.carpowersensor > 0
                condition1 = False
                condition2 = self.MoreThanStopThreshold and self.TotalEnergyThisHourIsNotZero
                if condition1 and not condition2:
                    return constants.CHARGECONTROLLER.Done
                elif condition2:
                    return constants.CHARGECONTROLLER.Stop
                else:
                    return constants.CHARGECONTROLLER.Start
            else:
                return constants.CHARGECONTROLLER.Error
