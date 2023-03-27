from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    PERCENTAGE
)
from peaqevcore.models.locale.enums.time_periods import TimePeriods

from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import POWERCONTROLS
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid


class GainLossSensor(SensorEntity):
    def __init__(self, hub, entry_id, timeperiod: TimePeriods):
        self.hub = hub
        self._entry_id = entry_id
        self._attr_name = f"{self.hub.hubname} gain/loss {timeperiod.value.lower()}"
        self._state = None
        self._raw_state = None
        self._timeperiod = timeperiod
        self._attr_icon = "mdi:cash-clock"
        self._attr_available = True

    @property
    def state(self) -> float:
        return self._state

    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE

    async def async_update(self) -> None:
        ret = await self.hub.gainloss.state(self._timeperiod)
        if self._state != round(ret * 100, 1):
            self._state = round(ret * 100, 1)
            self._raw_state = ret

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{nametoid(self._attr_name)}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)}}

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "raw_state": self._raw_state
        }
