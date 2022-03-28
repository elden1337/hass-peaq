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
    def __init__(self, hub) -> None:
        """Initialize a Peaq Binary sensor."""
        self._attr_name = f"{hub.NAME} Charger enabled"
        self._hub = hub
        self._attr_device_class = "none"

    @property
    def unique_id(self):
        return f"{DOMAIN.lower()}_{self._attr_name}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.HUB_ID)}}

    @property
    def is_on(self) -> bool:
        return self._hub.chargerenabled.value
    
class PeaqBinarySensorDone(BinarySensorEntity):  
    def __init__(self, hub) -> None:
        """Initialize a Peaq Binary sensor."""
        self._attr_name = f"{hub.NAME} Charging done"
        self._hub = hub
        self._attr_device_class = "none"

    @property
    def unique_id(self):
        return f"{DOMAIN.lower()}_{self._attr_name}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.HUB_ID)}}

    @property
    def is_on(self) -> bool:
        return self._hub.ChargingDone
