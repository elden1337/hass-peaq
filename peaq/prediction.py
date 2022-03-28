from datetime import datetime

class Prediction:
    def __init__(self, hub):
        self._hub = hub
    
    @property
    def PredictedEnergyThisHour(self) -> float:
        ret = 0.0
        poweravg = self._hub.powersensormovingaverage.value if self._hub.powersensormovingaverage.value is not None else 0
        if self._hub.TotalEnergyThisHour > 0 and (datetime.now().minute > 0 or (datetime.now().minute + datetime.now().second) > 30):
                ret = (((poweravg /60/60) * (3600 - ((datetime.now().minute *60)+datetime.now().second))+self._hub.TotalEnergyThisHour*1000)/1000)
        else:
            ret = poweravg / 1000
        return round(ret,3)
    
    @property
    def PredictedPercentageOfPeak(self) -> float:
        if self._hub.currentpeak.value == 0.0 or self._hub.currentpeak.value is None:
            return 0
        elif self.PredictedEnergyThisHour == 0.0 or self.PredictedEnergyThisHour is None:
            return 0
        return round((self.PredictedEnergyThisHour / self._hub.currentpeak.value) * 100,2)
