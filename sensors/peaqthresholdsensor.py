from homeassistant.const import PERCENTAGE
from custom_components.peaq.sensors.sensorbase import SensorBase

class PeaqThresholdSensor(SensorBase):
    _attr_unit_of_measurement = PERCENTAGE

    def __init__(self, hub):
        """Initialize the sensor."""
        name = f"{hub.hubname} Threshold"
        super().__init__(hub, name.lower())

        self._attr_name = name
        self._state = self._hub.prediction.predictedpercentageofpeak
        self._start_threshold = None
        self._stop_threshold = None
        
    @property
    def state(self):
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:stairs"

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