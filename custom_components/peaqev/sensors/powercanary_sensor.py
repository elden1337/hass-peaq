import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    ELECTRIC_CURRENT_AMPERE
)

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import POWERCANARY

_LOGGER = logging.getLogger(__name__)


class PowerCanaryDevice(SensorEntity):
    should_poll = True

    def __init__(self, hub, name: str, entry_id):
        self._hub = hub
        self._entry_id = entry_id
        self._attr_name = name
        self._attr_available = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._hub.hub_id, POWERCANARY)},
            "name": f"{DOMAIN} {POWERCANARY}",
            "sw_version": 1,
            "model": f"{self._hub.power_canary.fuse}",
            "manufacturer": "Peaq systems",
        }

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"


class PowerCanaryStatusSensor(PowerCanaryDevice):
    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {POWERCANARY} status"
        super().__init__(hub, name, entry_id)
        self._hub = hub
        self._state = self._hub.power_canary.state_string
        self._attr_icon = "mdi:bird"

    @property
    def state(self) -> int:
        return self._state

    def update(self) -> None:
        self._state = self._hub.power_canary.state_string


class PowerCanaryPercentageSensor(PowerCanaryDevice):
    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {POWERCANARY} current percentage"
        super().__init__(hub, name, entry_id)
        self._hub = hub
        self._state = None
        self._warning = None
        self._cutoff = None
        self._attr_icon = "mdi:fuse-alert"
        self.update()

    @property
    def state(self) -> float:
        return self._state

    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE

    def update(self) -> None:
        self._state = round(self._hub.power_canary.current_percentage * 100,2)
        self._warning = round(self._hub.power_canary.warning_threshold * 100,2)
        self._cutoff = round(self._hub.power_canary.cutoff_threshold * 100,2)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "warning_threshold": self._warning,
            "cutoff_threshold": self._cutoff
        }


class PowerCanaryMaxAmpSensor(PowerCanaryDevice):
    device_class = SensorDeviceClass.ENERGY
    unit_of_measurement = ELECTRIC_CURRENT_AMPERE

    def __init__(self, hub, entry_id):
        name = f"{hub.hubname} {POWERCANARY} allowed amps"
        super().__init__(hub, name, entry_id)
        self._hub = hub
        self._state = None
        self._attr_icon = "mdi:sine-wave"
        self.update()

    @property
    def state(self) -> int:
        return self._state

    def update(self) -> None:
        self._state = max(self._hub.power_canary.threephase_amps.values())



