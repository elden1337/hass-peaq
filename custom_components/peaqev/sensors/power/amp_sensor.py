from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import ELECTRIC_CURRENT_AMPERE

from custom_components.peaqev.peaqservice.util.constants import ALLOWEDCURRENT
from custom_components.peaqev.sensors.sensorbase import PowerDevice

_LOGGER = logging.getLogger(__name__)


class PeaqAmpSensor(PowerDevice):
    device_class = SensorDeviceClass.ENERGY
    unit_of_measurement = ELECTRIC_CURRENT_AMPERE

    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f"{hub.hubname} {ALLOWEDCURRENT}"
        super().__init__(hub, name, entry_id)
        self.hub = hub
        self._state = None
        self._attr_icon = "mdi:current-ac"
        self._charger_current = 0
        self._charger_phases = None
        self._all_currents = None

    @property
    def state(self) -> int:
        return self._state

    async def async_update(self) -> None:
        if self.hub.is_initialized:
            self._state = await self.hub.threshold.async_allowed_current()  # todo: composition
            await self.hub.sensors.chargerobject_switch.async_updatecurrent()
            self._charger_current = self.hub.sensors.chargerobject_switch.current
            self._charger_phases = self.hub.threshold.phases  # todo: composition
            self._all_currents = list(self.hub.threshold.currents.values())  # todo: composition

    @property
    def extra_state_attributes(self) -> dict:
        curr = self._charger_current if self._charger_current > 0 else "unreachable"
        return {
            "charger_reported_current": curr,
            "peaqev phase-setting": self._charger_phases,
            "allowed current-list": self._all_currents,
        }
