from homeassistant.components.sensor import SensorEntity
from custom_components.peaq.const import DOMAIN

class SensorBase(SensorEntity):
    should_poll = True

    def __init__(self, hub, name:str):
        """Initialize the sensor."""
        self._hub = hub
        self._attr_name = name.lower().replace(" ", "_")
        self._attr_unique_id = f"{DOMAIN}_{self._hub.HUB_ID}_{self._attr_name}"
        self._attr_available = True
        
    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._hub.HUB_ID)}}

    # @property
    # def unique_id(self): 
    #     return self._attr_unique_id