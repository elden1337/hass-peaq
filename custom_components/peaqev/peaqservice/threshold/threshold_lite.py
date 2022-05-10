from datetime import datetime
from custom_components.peaqev.peaqservice.threshold.thresholdbase import ThresholdBase
from peaqevcore.Threshold import ThresholdBase as _core
import logging

_LOGGER = logging.getLogger(__name__)


class ThresholdLite(ThresholdBase):
    def __init__(self, hub):
        self._hub = hub
        super().__init__(hub)

    @property
    def allowedcurrent(self) -> int:
        pass
        # amps = self._setcurrentdict()
        # return _core.allowedcurrent(
        #     datetime.now().minute,
        #     self._hub.powersensormovingaverage.value if self._hub.powersensormovingaverage.value is not None else 0,
        #     self._hub.charger_enabled.value,
        #     self._hub.charger_done.value,
        #     amps,
        #     self._hub.totalhourlyenergy.value,
        #     self._hub.current_peak_dynamic
        # )


