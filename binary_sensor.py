
from .const import (
    DOMAIN)

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
# from homeassistant.helpers.entity_platform import AddEntitiesCallback

async def async_setup_entry(hass : HomeAssistant, config_entry, async_add_entities):
    hub = hass.data[DOMAIN]["hub"]

    peaqsensors = []
    
    peaqsensors.append(PeaqBinarySensor(hub, "Charging done", "none", hub.charging_done))
    peaqsensors.append(PeaqBinarySensor(hub, "Charger enabled", "none"))
    async_add_entities(peaqsensors)

class PeaqBinarySensor(BinarySensorEntity):  
    
    should_poll = True

    def __init__(self, hub, name, deviceclass, internalsensor = None) -> None:
        """Initialize a Peaq Binary sensor."""
        self._name = f"{hub.NAME} {name}"
        self._sensor = internalsensor if internalsensor is not None else None
        self._state = "on" if self._sensor == True else "off"
        self.hub = hub
        self._deviceclass = deviceclass

    @property
    def unique_id(self):
        return f"{DOMAIN.lower()}_{self._name}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.hub.HUB_ID)}}

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_on(self) -> bool:
        return True if self._state == "on" else False

    @property
    def device_class(self):
        return self._deviceclass

    def update(self) -> None:
        self._state = "on" if self._sensor == True else "off"
