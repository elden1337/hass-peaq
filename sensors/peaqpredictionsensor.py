from custom_components.peaq.sensors.sensorbase import SensorBase

from homeassistant.const import (
    DEVICE_CLASS_ENERGY,
    ENERGY_KILO_WATT_HOUR
)

class PeaqPredictionSensor(SensorBase):
    device_class = DEVICE_CLASS_ENERGY
    unit_of_measurement = ENERGY_KILO_WATT_HOUR

    def __init__(self, hub):
        name = f"{hub.NAME} Prediction"
        super().__init__(hub, name.lower())

        self._attr_name = name
        self._state = self._hub.Prediction.PredictedEnergyThisHour

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._hub.Prediction.PredictedEnergyThisHour

    @property
    def icon(self) -> str:
        return "mdi:magic-staff"