import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ENERGY_KILO_WATT_HOUR
)

from custom_components.peaqev.peaqservice.util.constants import PREDICTION
from custom_components.peaqev.sensors.sensorbase import PowerDevice

_LOGGER = logging.getLogger(__name__)

class PeaqPredictionSensor(PowerDevice):
    device_class = SensorDeviceClass.ENERGY
    unit_of_measurement = ENERGY_KILO_WATT_HOUR

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {PREDICTION}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = None

    @property
    def state(self):
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:magic-staff"

    def update(self) -> None:
        if self.hub.is_initialized:
            self._state = self.hub.prediction.predictedenergy  #todo: composition




