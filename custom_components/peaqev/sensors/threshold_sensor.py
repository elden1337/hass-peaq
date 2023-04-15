from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from homeassistant.const import PERCENTAGE

from custom_components.peaqev.peaqservice.util.constants import THRESHOLD
from custom_components.peaqev.sensors.sensorbase import PowerDevice


class PeaqThresholdSensor(PowerDevice):
    def __init__(self, hub:HomeAssistantHub, entry_id):
        name = f"{hub.hubname} {THRESHOLD}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = None
        self._start_threshold = None
        self._stop_threshold = None

    @property
    def state(self):
        try:
            return round(self._state, 1)
        except:
            return None

    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE

    @property
    def icon(self) -> str:
        return "mdi:chart-bell-curve"

    async def async_update(self) -> None:
        if not self.hub.is_initialized:
            return
        self._state = getattr(self.hub.prediction, "predictedpercentageofpeak")
        _start = getattr(self.hub.threshold, "start")
        _stop = getattr(self.hub.threshold, "stop")
        try:
            self._start_threshold = round(_start, 1)
        except:
            self._start_threshold = _start
        try:
            self._stop_threshold = round(_stop, 1)
        except:
            self._stop_threshold = _stop

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "start_threshold": self._start_threshold,
            "stop_threshold": self._stop_threshold,
        }
