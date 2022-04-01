from custom_components.peaq.sensors.sensorbase import SensorBase
from custom_components.peaq.peaq.constants import CHARGERCONTROLLER

class PeaqSensor(SensorBase):
    def __init__(self, hub):
        name = f"{hub.hubname} {CHARGERCONTROLLER}"
        super().__init__(hub, name)

        self._attr_name = name
        self._state = self._hub.chargecontroller.status.name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._hub.chargecontroller.status.name

    @property
    def icon(self) -> str:
        return "mdi:gate-xor"

    def update(self) -> None:
        self._state = self._hub.chargecontroller.status.name