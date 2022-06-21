import logging
from datetime import datetime

from peaqevcore.models.chargerstates import CHARGERSTATES
from peaqevcore.threshold_service.threshold import ThresholdBase as _core

from custom_components.peaqev.peaqservice.threshold.thresholdbase import ThresholdBase

_LOGGER = logging.getLogger(__name__)

class Threshold(ThresholdBase):
    def __init__(self, hub):
        self._hub = hub
        super().__init__(hub)

    @property
    def allowedcurrent(self) -> int:
        amps = self._setcurrentdict()
        if self._hub.chargecontroller.status is not CHARGERSTATES.Start.name:
            return min(amps.values())
        return _core.allowedcurrent(
            datetime.now().minute,
            self._hub.powersensormovingaverage.value if self._hub.powersensormovingaverage.value is not None else 0,
            self._hub.charger_enabled.value,
            self._hub.charger_done.value,
            amps,
            self._hub.totalhourlyenergy.value,
            self._hub.current_peak_dynamic,
            self._hub.locale.data.is_quarterly(self._hub.locale.data)
        )
