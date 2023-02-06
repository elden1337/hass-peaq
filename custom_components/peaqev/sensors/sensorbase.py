from homeassistant.components.sensor import SensorEntity

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import POWERCONTROLS, HUB


class PowerDevice(SensorEntity):
    should_poll = True

    def __init__(self, hub, name: str, entry_id):
        self._hub = hub
        self._entry_id = entry_id
        self._attr_name = name
        self._attr_available = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._hub.hub_id, POWERCONTROLS)},
            "name": f"{DOMAIN} {POWERCONTROLS}",
            "sw_version": 1,
            "manufacturer": "Peaq systems",
        }

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"


class SensorBase(SensorEntity):
    should_poll = True

    def __init__(self, hub, name: str, entry_id):
        """Initialize the sensor."""
        self._hub = hub
        self._entry_id = entry_id
        self._attr_name = name
        self._attr_available = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._hub.hub_id)},
            "name": f"{DOMAIN} {HUB}",
            "sw_version": 1,
            "model": f"{self._hub.sensors.locale.type} ({self._hub.chargertype.type.value})",
            "manufacturer": "Peaq systems",
        }

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"
