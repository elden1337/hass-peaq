import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import POWER_WATT

from custom_components.peaqev.sensors.sensorbase import PowerDevice

_LOGGER = logging.getLogger(__name__)


class PeaqHousePowerSensor(PowerDevice):
    device_class = SensorDeviceClass.POWER
    unit_of_measurement = POWER_WATT

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {hub.sensors.power.house.name}"  # todo: composition
        super().__init__(hub, name, entry_id)
        self.hub = hub
        self._state = None
        self._attr_icon = "mdi:home-lightning-bolt"

    @property
    def state(self) -> int:
        return self._state

    async def async_update(self) -> None:
        if self.hub.is_initialized:
            self._state = self.hub.sensors.power.house.value  # todo: composition
