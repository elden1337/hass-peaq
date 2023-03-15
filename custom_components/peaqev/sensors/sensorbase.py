from homeassistant.components.sensor import SensorEntity

from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import POWERCONTROLS, HUB
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid


class PowerDevice(SensorEntity):
    should_poll = True

    def __init__(self, hub, name: str, entry_id):
        self.hub = hub
        self._entry_id = entry_id
        self._attr_name = name
        self._attr_available = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)},
            "name": f"{DOMAIN} {POWERCONTROLS}",
            "sw_version": 1,
            "manufacturer": "Peaq systems",
        }

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{nametoid(self._attr_name)}"


class SensorBase(SensorEntity):
    should_poll = True

    def __init__(self, hub, name: str, entry_id):
        """Initialize the sensor."""
        self.hub = hub
        self._entry_id = entry_id
        self._attr_name = name
        self._attr_available = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.hub.hub_id)},
            "name": f"{DOMAIN} {HUB}",
            "sw_version": 1,
            "model": f"{self.hub.sensors.locale.type} ({self.hub.chargertype.type.value})",  #todo: composition
            "manufacturer": "Peaq systems",
        }

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{nametoid(self._attr_name)}"
