from homeassistant.components.sensor import SensorEntity
from custom_components.peaq.const import DOMAIN
import custom_components.peaq.peaq.extensionmethods as ex

class SensorBase(SensorEntity):
    should_poll = True

    def __init__(self, hub, name:str):
        """Initialize the sensor."""
        self._hub = hub
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{self._hub.hub_id}_{ex.nametoid(self._attr_name)}"
        self._attr_available = True
        
    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}
