from datetime import datetime
import custom_components.peaq.peaq.constants as constants

class Threshold:
    def __init__(self, hub):
        self._hub = hub
        
    @property
    def Stop(self) -> float:
        nowmin = datetime.now().minute
        stopthreshold = (((nowmin+pow(1.071,nowmin))*0.00165)+0.8) * 100
        if str(datetime.now().hour) in self._hub.CautionHours and nowmin < 45:
            stopthreshold = (((nowmin+pow(1.075,nowmin))*0.0032)+0.7) * 100
        return round(stopthreshold,2) 

    @property
    def Start(self) -> float:
        nowmin = datetime.now().minute
        startthreshold = (((nowmin+pow(1.066,nowmin))*0.0045)+0.5) * 100
        if str(datetime.now().hour) in self._hub.CautionHours and nowmin < 45:
            startthreshold = (((nowmin+pow(1.081,nowmin))*0.0049)+0.4) * 100
        return round(startthreshold,2)
    
    @property
    def AllowedCurrent(self) -> int:
        ret = 6
        nowmin = datetime.now().minute
        for key, value in constants.CURRENTS.items():
            if (((((self._hub.powersensormovingaverage.value + key if self._hub.powersensormovingaverage.value is not None else key) / 60) * (60-nowmin)+ self._hub.TotalEnergyThisHour*1000)/1000) < self._hub.currentpeak.value):
                ret = value
                break
        return ret