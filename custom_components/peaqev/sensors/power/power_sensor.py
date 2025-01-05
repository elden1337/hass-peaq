from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfPower

from custom_components.peaqev.sensors.sensorbase import PowerDevice

_LOGGER = logging.getLogger(__name__)


class PeaqPowerSensor(PowerDevice):
    device_class = SensorDeviceClass.POWER
    unit_of_measurement = UnitOfPower.WATT

    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f'{hub.hubname} {hub.sensors.power.total.name}'  # todo: composition
        super().__init__(hub, name, entry_id)
        self.hub = hub
        self._state = None
        self._attr_icon = 'mdi:flash'

    @property
    def state(self) -> int:
        try:
            return int(self._state)
        except (ValueError, TypeError):
            if self._state is not None:
                _LOGGER.error('Could not parse state %s for powersensor', self._state)
            return 0

    async def async_update(self) -> None:
        new_state = self.hub.sensors.power.total.value
        if isinstance(new_state, (int, float)):
            if abs(new_state - self.state) > 3:
                self._state = new_state
