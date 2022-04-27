from datetime import datetime
import custom_components.peaqev.peaqservice.util.constants as constants
from peaqevcore.Threshold import ThresholdBase as _core


class Threshold():
    def __init__(self, hub):
        self._hub = hub

    @property
    def stop(self) -> float:
        return _core.stop(
            datetime.now().minute,
            str(datetime.now().hour) in self._hub.hours.caution_hours
        )

    @property
    def start(self) -> float:
        return _core.start(
            datetime.now().minute,
            str(datetime.now().hour) in self._hub.hours.caution_hours
        )

    @property
    def allowedcurrent(self) -> int:
        return _core.allowedcurrent(
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