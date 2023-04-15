from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import ENERGY_KILO_WATT_HOUR

from custom_components.peaqev.peaqservice.util.constants import PREDICTION
from custom_components.peaqev.sensors.sensorbase import PowerDevice

_LOGGER = logging.getLogger(__name__)


class PeaqPredictionSensor(PowerDevice):
    device_class = SensorDeviceClass.ENERGY
    unit_of_measurement = ENERGY_KILO_WATT_HOUR

    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f"{hub.hubname} {PREDICTION}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = None

    @property
    def state(self):
        try:
            return round(float(self._state), 1)
        except:
            return self._state

    @property
    def icon(self) -> str:
        return "mdi:magic-staff"

    async def async_update(self) -> None:
        if self.hub.is_initialized:
            self._state = getattr(self.hub.prediction, "predictedenergy")
