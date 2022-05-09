from homeassistant.components.sensor import SensorEntity
from custom_components.peaqev.const import DOMAIN
import custom_components.peaqev.peaqservice.util.extensionmethods as ex

class SensorBase(SensorEntity):
    should_poll = True

    def __init__(self, hub, name:str, entry_id):
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

class MoneySensor(SensorEntity):
    should_poll = True

    def __init__(self, hub, name: str):
        """Initialize the sensor."""
        self._hub = hub
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{self._hub.hub_id}_{ex.nametoid(self._attr_name)}"
        self._attr_available = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._hub.hub_id, "money")},
            "name": f"{self._attr_name} money",
            "sw_version": 1,
            "model": f"{self._hub.locale.type} ({self._hub.chargertype.type})",
            "manufacturer": "Peaq systems",
        }