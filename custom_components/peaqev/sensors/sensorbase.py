from homeassistant.components.sensor import SensorEntity

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN


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
            "name": self._attr_name,
            "sw_version": 1,
            "model": f"{self._hub.locale.type} ({self._hub.chargertype.type})",
            "manufacturer": "Peaq systems",
        }

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"
