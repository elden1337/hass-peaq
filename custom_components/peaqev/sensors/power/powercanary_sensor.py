from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import ELECTRIC_CURRENT_AMPERE, PERCENTAGE

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import POWERCANARY

_LOGGER = logging.getLogger(__name__)


class PowerCanaryDevice(SensorEntity):
    should_poll = True

    def __init__(self, hub: HomeAssistantHub, name: str, entry_id):
        self.hub = hub
        self._entry_id = entry_id
        self._attr_name = name
        self._attr_available = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.hub.hub_id, POWERCANARY)},
            "name": f"{DOMAIN} {POWERCANARY}",
            "sw_version": 1,
            "model": f"{self.hub.power.power_canary.fuse}",  # todo: composition
            "manufacturer": "Peaq systems",
        }

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"


class PowerCanaryStatusSensor(PowerCanaryDevice):
    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f"{hub.hubname} {POWERCANARY} status"
        super().__init__(hub, name, entry_id)
        self._state = None
        self._attr_icon = "mdi:bird"

    @property
    def state(self) -> int:
        return self._state

    async def async_update(self) -> None:
        if self.hub.is_initialized:
            self._state = self.hub.power.power_canary.state_string  # todo: composition


class PowerCanaryPercentageSensor(PowerCanaryDevice):
    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f"{hub.hubname} {POWERCANARY} current percentage"
        super().__init__(hub, name, entry_id)
        self._state = None
        self._warning = None
        self._cutoff = None
        self._attr_icon = "mdi:fuse-alert"

    @property
    def state(self) -> float:
        return self._state

    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE

    async def async_update(self) -> None:
        if not self.hub.is_initialized:
            return
        if int(self.hub.power.power_canary.current_percentage * 100) != self._state:  # todo: composition
            self._state = int(self.hub.power.power_canary.current_percentage * 100)  # todo: composition
        self._warning = round(
            self.hub.power.power_canary.model.warning_threshold * 100, 2
        )  # todo: composition
        self._cutoff = round(self.hub.power.power_canary.model.cutoff_threshold * 100, 2)  # todo: composition

    @property
    def extra_state_attributes(self) -> dict:
        return {"warning_threshold": self._warning, "cutoff_threshold": self._cutoff}


class PowerCanaryMaxAmpSensor(PowerCanaryDevice):
    device_class = SensorDeviceClass.ENERGY
    unit_of_measurement = ELECTRIC_CURRENT_AMPERE

    def __init__(self, hub: HomeAssistantHub, entry_id, phases: int):
        name = f"{hub.hubname} {POWERCANARY} allowed amps {phases}-phase"
        super().__init__(hub, name, entry_id)
        self._state = None
        self._attr_icon = "mdi:sine-wave"
        self.phases = phases

    @property
    def state(self) -> int:
        return self._state

    async def async_update(self) -> None:
        if not self.hub.is_initialized:
            return
        ret = {}
        if self.phases == 1:
            ret = getattr(self.hub.power.power_canary, "onephase_amps", {})
        if self.phases == 3:
            ret = getattr(self.hub.power.power_canary, "threephase_amps", {})
        if len(ret):
            self._state = max(ret.values())
        else:
            _LOGGER.debug("No data for %s", self.name)
