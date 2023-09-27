from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

from homeassistant.components.sensor import SensorDeviceClass

from custom_components.peaqev.sensors.money_sensor_helpers import *
from custom_components.peaqev.sensors.sensorbase import MoneyDevice

_LOGGER = logging.getLogger(__name__)


class PeaqSimpleMoneySensor(MoneyDevice):
    device_class = SensorDeviceClass.MONETARY

    def __init__(self, hub: HomeAssistantHub, entry_id, sensor_name: str, caller_attribute: str):
        name = f"{hub.hubname} {sensor_name}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = None
        self._caller_attribute = caller_attribute
        self._use_cent = None
        self._attr_unit_of_measurement = None

    @property
    def state(self):
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:car-clock"

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

    async def async_update(self) -> None:
        self._use_cent = self.hub.spotprice.use_cent
        self._attr_unit_of_measurement = getattr(self.hub.spotprice, "currency")
        ret = getattr(self.hub.spotprice, self._caller_attribute)
        if ret is not None:
            self._state = ret if not self._use_cent else ret / 100

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "Use Cent": self._use_cent
        }

