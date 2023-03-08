import logging
from datetime import timedelta

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=4)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities): # pylint:disable=unused-argument
    hub = hass.data[DOMAIN]["hub"]

    switches = [
        {
            "name": "Charger enabled",
            "entity": "charger_enabled"
        }
    ]

    async_add_entities(PeaqSwitch(s, hub) for s in switches)

class PeaqSwitch(SwitchEntity, RestoreEntity):
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
        return self._state is True

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    def turn_on(self):
        self._hub.observer.broadcast("update charger enabled", True)

    def turn_off(self):
        self._hub.observer.broadcast("update charger enabled", False)

    def update(self):
        new_state = self._hub.enabled
        self.state = "on" if new_state is True else "off"

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        if state:
            self._state = state.state
            self._hub.observer.broadcast("update charger enabled", self._state)
        else:
            self._state = self._hub.enabled
