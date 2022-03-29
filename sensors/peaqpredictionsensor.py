from custom_components.peaq.sensors.sensorbase import SensorBase

from homeassistant.const import (
    DEVICE_CLASS_ENERGY,
    ENERGY_KILO_WATT_HOUR
)

class PeaqPredictionSensor(SensorBase):
    device_class = DEVICE_CLASS_ENERGY
    unit_of_measurement = ENERGY_KILO_WATT_HOUR

    def __init__(self, hub):
        name = f"{hub.hubname} Prediction"
        super().__init__(hub, name.lower())

        self._attr_name = name
        self._state = self._hub.prediction.predictedenergy

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._hub.prediction.predictedenergy

    @property
    def icon(self) -> str:
        return "mdi:magic-staff"

    def update(self) -> None:
        self._state = self._hub.prediction.predictedenergy