from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.peaqev.peaqservice.hub.sensors.models.ema import EMA

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import POWER_WATT

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import POWERCONTROLS

_LOGGER = logging.getLogger(__name__)


class PeaqAverageSensor(SensorEntity, RestoreEntity):
    device_class = SensorDeviceClass.POWER
    unit_of_measurement = POWER_WATT

    def __init__(self, hub: HomeAssistantHub, entry_id, name, max_age):
        self.hub = hub
        self._entry_id = entry_id
        self._attr_name = f"{hub.hubname} {name}"
        self._state = None
        self._avg = EMA(max_age)

    @property
    def state(self):
        return self._state

    async def async_update(self) -> None:
        data = self.hub.state_machine.states.get(self.hub.sensors.power.house.entity)
        if data:
            try:
                floatdata = float(data.state)
                if isinstance(floatdata, float):
                    self._state = self._avg.average(floatdata)
                else:
                    _LOGGER.debug(f"Could not convert {data.state} to float.")
            except:
                pass

    async def async_added_to_hass(self) -> None:
        state = await super().async_get_last_state()
        _LOGGER.debug("last state of %s = %s", self._attr_name, state)
        if state:
            self._state = float(state.state)
            self._avg.imported_average = float(state.state)

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)}}

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"

