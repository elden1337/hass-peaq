import logging

from homeassistant.helpers.restore_state import RestoreEntity

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)


class PeaqScheduleSensor(SensorBase, RestoreEntity):
    def __init__(self, hub, entry_id):
        self._name = f"{hub.hubname} schedules"
        self._state = ""
        self._schedules = {}
        super().__init__(hub, self._name, entry_id)

    @property
    def state(self) -> str:
        return self._state

    def update(self) -> None:
        self._state = ""
        self._schedules = {}


    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {}
        attr_dict["schedules"] = self._schedules
        return attr_dict

    @property
    def icon(self) -> str:
        return "mdi:home-clock-outline"

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._name)}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        if state:
            self._state = state.state
            self._schedules = state.attributes.get('schedules', 50)
            #self._hub.sensors.locale.data.query_model.peaks.set_init_dict(self._peaks_dict)
        else:
            self._state = ""
            self._schedules = {}
