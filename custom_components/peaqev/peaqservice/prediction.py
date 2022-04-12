from datetime import datetime

class Prediction:
    def __init__(self, hub):
        self._hub = hub
    
    @property
    def predictedenergy(self) -> float:
        nowmin = datetime.now().minute
        nowsec = datetime.now().second
        poweravg = self._hub.powersensormovingaverage.value if self._hub.powersensormovingaverage.value is not None else 0
        if self._hub.totalhourlyenergy.value > 0 and (nowmin > 0 or (nowmin + nowsec) > 30):
            ret = (((poweravg / 60 / 60) * (3600 - ((nowmin * 60)+nowsec))+self._hub.totalhourlyenergy.value*1000)/1000)
        else:
            ret = poweravg / 1000
        return round(ret, 3)
    
    @property
    def predictedpercentageofpeak(self) -> float:
        if self._hub.currentpeak.value == 0.0 or self._hub.currentpeak.value is None:
            return 0
        elif self.predictedenergy == 0.0 or self.predictedenergy is None:
            return 0
        return round((self.predictedenergy / self._hub.currentpeak.value) * 100, 2)
