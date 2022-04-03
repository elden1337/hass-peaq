from custom_components.peaqev.sensors.sensorbase import SensorBase
from custom_components.peaqev.peaqservice.constants import CHARGERCONTROLLER

class PeaqSensor(SensorBase):
    def __init__(self, hub):
        name = f"{hub.hubname} {CHARGERCONTROLLER}"
        super().__init__(hub, name)

        self._attr_name = name
        self._state = self._hub.chargecontroller.status.name

    @property
    def state(self):
        return self._hub.chargecontroller.status.name

    @property
    def icon(self) -> str:
        return "mdi:gate-xor"

    def update(self) -> None:
        self._state = self._hub.chargecontroller.status.name