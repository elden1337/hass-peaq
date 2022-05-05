from homeassistant.const import PERCENTAGE
from custom_components.peaqev.sensors.sensorbase import SensorBase
from custom_components.peaqev.peaqservice.util.constants import THRESHOLD

class PeaqThresholdSensor(SensorBase):

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {THRESHOLD}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = self._hub.prediction.predictedpercentageofpeak
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
        self._start_threshold = self._hub.threshold.start
        self._stop_threshold = self._hub.threshold.stop
        self._state = self._hub.prediction.predictedpercentageofpeak

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "start_threshold": self._start_threshold,
            "stop_threshold": self._stop_threshold,
        }