import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities): # pylint:disable=unused-argument
    hub = hass.data[DOMAIN]["hub"]

    switches = [
        {
            "name": "Charger enabled",
            "entity": "charger_enabled"
        }
    ]

    async_add_entities(PeaqSwitch(s, hub) for s in switches)

class PeaqSwitch(SwitchEntity):
    def __init__(self, switch, hub) -> None:
        """Initialize a PeaqSwitch."""
        self._switch = switch
        self._attr_name = f"{hub.hubname} {self._switch['name']}"
        self._hub = hub
        self._attr_device_class = "none"
        self._state = None

    @property
    def unique_id(self):
        """The unique id used by Home Assistant"""
        return f"{DOMAIN.lower()}_{self._attr_name}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}

    @property
    def is_on(self) -> bool:
        return self._hub.charger_enabled.value

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    def turn_on(self):
        self._hub.charger_enabled.value = True

    def turn_off(self):
        self._hub.charger_enabled.value = False

    def update(self):
        new_state = self._hub.charger_enabled.value
        self.state = "on" if new_state is True else "off"
