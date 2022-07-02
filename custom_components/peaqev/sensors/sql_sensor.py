import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ENERGY_KILO_WATT_HOUR
)
from homeassistant.helpers.restore_state import RestoreEntity

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)

class PeaqPeakSensor(SensorBase, RestoreEntity):
    device_class = SensorDeviceClass.ENERGY
    unit_of_measurement = ENERGY_KILO_WATT_HOUR
    def __init__(self, hub, entry_id):
        self._name = f"{hub.hubname} peak"
        self._charged_peak = 0
        self._peaks_dict: dict| None
        self._observed_peak = 0
        super().__init__(hub, self._name, entry_id)

    @property
    def state(self) -> float:
        return float(self._charged_peak)

    def update(self) -> None:
        self._charged_peak = self._hub.locale.data.query_model.charged_peak
        self._peaks_dict = self._hub.locale.data.query_model.peaks.export_peaks
        self._observed_peak = self._hub.locale.data.query_model.observed_peak

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {}
        attr_dict["observed_peak"] = float(self._observed_peak)
        attr_dict["peaks_dictionary"] = self.set_peaksdict()
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
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}

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
            self._peaks_dict = state.attributes.get('peaks_dictionary', 50)
            self._hub.locale.data.query_model.peaks.set_init_dict(self._peaks_dict)
            self._observed_peak = state.attributes.get('observed_peak', 50)
        else:
            self._charged_peak = 0
            self._peaks_dict = {}
            self._observed_peak = 0
