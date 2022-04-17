from datetime import datetime
import custom_components.peaqev.peaqservice.util.constants as constants
from custom_components.peaqev.peaqservice.threshold.thresholdbase import ThresholdBase


class Threshold(ThresholdBase):
    def __init__(self, hub):
        self._hub = hub

    @property
    def stop(self) -> float:
        return self._stop(
            datetime.now().minute,
            str(datetime.now().hour) in self._hub.cautionhours
        )

    @property
    def start(self) -> float:
        return self._start(
            datetime.now().minute,
            str(datetime.now().hour) in self._hub.cautionhours
        )

    @property
    def allowedcurrent(self) -> int:
        return self._allowedcurrent(
            datetime.now().minute,
            self._hub.powersensormovingaverage.value if self._hub.powersensormovingaverage.value is not None else 0,
            self._hub.charger_enabled.value,
            self._hub.charger_done.value,
            self._setcurrentdict(),
            self._hub.totalhourlyenergy.value,
            self._hub.currentpeak.value
        )

    # this one must be done better. Currently cannot accommodate 1-32A single phase for instance.
    def _setcurrentdict(self):
        if int(self._hub.carpowersensor.value) > 3700:
            return constants.CURRENTS_THREEPHASE_1_16
        return constants.CURRENTS_ONEPHASE_1_16