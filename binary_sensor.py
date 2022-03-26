from .const import (
    DOMAIN)

from homeassistant.components.binary_sensor import BinarySensorEntity, ENTITY_ID_FORMAT
from homeassistant.core import HomeAssistant

async def async_setup_entry(hass : HomeAssistant, config_entry, async_add_entities):
    hub = hass.data[DOMAIN]["hub"]

    peaqsensors = []
    
    peaqsensors.append(PeaqBinarySensorDone(hub))
    peaqsensors.append(PeaqBinarySensorEnabled(hub))
    async_add_entities(peaqsensors)

class PeaqBinarySensorEnabled(BinarySensorEntity):  
    #should_poll = True

    def __init__(self, hub) -> None:
        """Initialize a Peaq Binary sensor."""
        self._attr_name = f"{hub.NAME} Charger enabled"
        self.hub = hub
        self._attr_device_class = "none"
        #self._state = "on" if hub.ChargerEnabled == True else False

    @property
    def unique_id(self):
        return f"{DOMAIN.lower()}_{self._attr_name}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.hub.HUB_ID)}}

    @property
    def is_on(self) -> bool:
        return self.hub.ChargerEnabled

    # def update(self) -> None: 
    #     self._state = "on" if self.hub.ChargerEnabled == True else False


class PeaqBinarySensorDone(BinarySensorEntity):  
    #should_poll = True

    def __init__(self, hub) -> None:
        """Initialize a Peaq Binary sensor."""
        self._attr_name = f"{hub.NAME} Charging done"
        self.hub = hub
        self._attr_device_class = "none"
        #self._state = "on" if hub.ChargingDone == True else False
        #super().__init__(system, parameter_id, None, ENTITY_ID_FORMAT)

    @property
    def unique_id(self):
        return f"{DOMAIN.lower()}_{self._attr_name}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.hub.HUB_ID)}}

    @property
    def is_on(self) -> bool:
        return self.hub.ChargingDone

    # def update(self) -> None:
    #     self._state = "on" if self.hub.ChargingDone == True else False
