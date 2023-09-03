from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import ENERGY_KILO_WATT_HOUR
from homeassistant.helpers.restore_state import RestoreEntity

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)


class PeaqPeakSensor(SensorBase, RestoreEntity):
    device_class = SensorDeviceClass.ENERGY
    unit_of_measurement = ENERGY_KILO_WATT_HOUR

    def __init__(self, hub:HomeAssistantHub, entry_id):
        self._name = f"{hub.hubname} peak"
        self._charged_peak = 0
        self._peaks_dict: dict = {}
        self._observed_peak = 0
        self._history: dict = {}
        super().__init__(hub, self._name, entry_id)

    @property
    def state(self) -> float:
        try:
            return round(float(self._charged_peak), 1)
        except:
            return 0

    async def async_update(self) -> None:
        self._charged_peak = getattr(self.hub.sensors.locale.data.query_model, "charged_peak")
        _peaks_dict = getattr(self.hub.sensors.locale.data.query_model.peaks, "export_peaks")
        if self._peaks_dict != _peaks_dict:
            #_LOGGER.debug("updating peaks_dict frontend.")
            self._peaks_dict = _peaks_dict
        _observed = getattr(self.hub.sensors.locale.data.query_model, "observed_peak")
        self._observed_peak = self.hub.sensors.current_peak.value
        self._history = self.hub.sensors.current_peak.history

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {
            "observed_peak": float(self._observed_peak),
            "peaks_dictionary": self.set_peaksdict(),
            "peaks_history": self._history,
        }
        if self.hub.options.use_peak_history:
            attr_dict["Use startpeak from last year"] = True
        return attr_dict

    @property
    def icon(self) -> str:
        return "mdi:chart-donut-variant"

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._name)}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.hub.hub_id)}}

    def set_peaksdict(self) -> dict:
        ret = {}
        if len(self._peaks_dict) > 0:
            ret["m"] = self._peaks_dict["m"]
            ret["p"] = self._peaks_dict["p"]
        return ret

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        if state:
            _LOGGER.debug("last state of %s = %s", self._name, state)
            self._charged_peak = state.state
            self._peaks_dict = state.attributes.get("peaks_dictionary", {})
            await self.hub.async_set_init_dict(self._peaks_dict)
            self._observed_peak = state.attributes.get("observed_peak", 0)
            self._history = state.attributes.get("peaks_history", {})
            if len(self._history):
                self.hub.sensors.current_peak.import_from_service(self._history)
        else:
            self._charged_peak = 0
            self._peaks_dict = {}
            self._observed_peak = 0
