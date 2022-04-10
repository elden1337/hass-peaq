from datetime import datetime
import custom_components.peaqev.peaqservice.constants as constants

class Threshold:
    def __init__(self, hub):
        self._hub = hub
        
    @property
    def stop(self) -> float:
        nowmin = datetime.now().minute
        stopthreshold = (((nowmin+pow(1.071,nowmin))*0.00165)+0.8) * 100
        if str(datetime.now().hour) in self._hub.cautionhours and nowmin < 45:
            stopthreshold = (((nowmin+pow(1.075,nowmin))*0.0032)+0.7) * 100
        return round(stopthreshold,2) 

    @property
    def start(self) -> float:
        nowmin = datetime.now().minute
        startthreshold = (((nowmin+pow(1.066,nowmin))*0.0045)+0.5) * 100
        if str(datetime.now().hour) in self._hub.cautionhours and nowmin < 45:
            startthreshold = (((nowmin+pow(1.081,nowmin))*0.0049)+0.4) * 100
        return round(startthreshold,2)
    
    @property
    def allowedcurrent(self) -> int:
        ret = 6
        nowmin = datetime.now().minute
        currents = self._setcurrentdict()
        for key, value in currents.items():
            if (((((self._hub.powersensormovingaverage.value + key if self._hub.powersensormovingaverage.value is not None else key) / 60) * (60-nowmin)+ self._hub.totalhourlyenergy.value*1000)/1000) < self._hub.currentpeak.value):
                ret = value
                break
        return ret


    def _setcurrentdict(self):
        if int(self._hub.carpowersensor.value) > 3700:
            return constants.CURRENTS_THREEPHASE_1_16
        return constants.CURRENTS_ONEPHASE_1_16