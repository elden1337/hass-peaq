from homeassistant.const import PERCENTAGE

from custom_components.peaqev.peaqservice.util.constants import THRESHOLD
from custom_components.peaqev.sensors.sensorbase import PowerDevice


class PeaqThresholdSensor(PowerDevice):

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {THRESHOLD}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = self.hub.prediction.predictedpercentageofpeak  #todo: composition
        self._start_threshold = None
        self._stop_threshold = None

    @property
    def state(self):
        return self._state

    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE

    @property
    def icon(self) -> str:
        return "mdi:chart-bell-curve"

    def update(self) -> None:
        self._start_threshold = self.hub.threshold.start  #todo: composition
        self._stop_threshold = self.hub.threshold.stop  #todo: composition
        self._state = self.hub.prediction.predictedpercentageofpeak  #todo: composition

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "start_threshold": self._start_threshold,
            "stop_threshold": self._stop_threshold,
        }
