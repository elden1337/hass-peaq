from datetime import datetime
import custom_components.peaqev.peaqservice.util.constants as constants

class Threshold:
    def __init__(self, hub):
        self._hub = hub

    @property
    def stop(self) -> float:
        nowmin = datetime.now().minute
        if str(datetime.now().hour) in self._hub.cautionhours and nowmin < 45:
            ret = (((nowmin+pow(1.075, nowmin)) * 0.0032) + 0.7)
        else:
            ret = (((nowmin + pow(1.071, nowmin)) * 0.00165) + 0.8)
        return round(ret * 100, 2)

    @property
    def start(self) -> float:
        nowmin = datetime.now().minute
        if str(datetime.now().hour) in self._hub.cautionhours and nowmin < 45:
            ret = (((nowmin+pow(1.081, nowmin)) * 0.0049) + 0.4)
        else:
            ret = (((nowmin + pow(1.066, nowmin)) * 0.0045) + 0.5)
        return round(ret * 100, 2)
    
    @property
    def allowedcurrent(self) -> int:
        nowmin = datetime.now().minute
        movingavg = self._hub.powersensormovingaverage.value if self._hub.powersensormovingaverage.value is not None else 0
        ret = 6
        if self._hub.charger_enabled.value is False or self._hub.charger_done.value is True or movingavg == 0:
            return ret
        currents = self._setcurrentdict()
        for key, value in currents.items():
            if ((((movingavg + key) / 60) * (60 - nowmin) + self._hub.totalhourlyenergy.value * 1000) / 1000) < self._hub.currentpeak.value:
                ret = value
                break
        return ret

    # this one must be done better. Currently cannot accommodate 1-32A single phase for instance.
    def _setcurrentdict(self):
        if int(self._hub.carpowersensor.value) > 3700:
            return constants.CURRENTS_THREEPHASE_1_16
        return constants.CURRENTS_ONEPHASE_1_16