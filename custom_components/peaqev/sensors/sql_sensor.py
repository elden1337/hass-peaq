from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sql.sensor import (
    SQLSensor
)

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.sensors.sensorbase import SensorBase


class PeaqSQLSensor(SQLSensor):
    def __init__(self, hub, sessmaker, query, entry_id):
        self._hub = hub
        self._attr_name = f"{hub.hubname} {query['name']}"
        self._entry_id = entry_id
        sm = sessmaker
        super().__init__(
            self._attr_name,
            sm,
            query["query"],
            "state",
            "kWh",
            None,
            entry_id
            )

    @property
    def icon(self) -> str:
        return "mdi:chart-arc"

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}

class PeaqPeakSensor(SensorBase):
    device_class = SensorDeviceClass.POWER

    def __init__(self, hub, entry_id):
        self._name = f"{hub.hubname} peak"
        self._unit_of_measurement = "kWh"
        self._charged_peak = 0
        self._peaks_dict = {}
        self._observed_peak = 0
        super().__init__(hub, self._name, entry_id)

    @property
    def state(self):
        return self._charged_peak

    def update(self) -> None:
        self._charged_peak = self._hub.locale.data.query_model.charged_peak
        self._peaks_dict = self._hub.locale.data.query_model.peaks
        self._observed_peak = self._hub.locale.data.query_model.observed_peak

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {}
        attr_dict["observed_peak"] = self._observed_peak
        attr_dict["peaks_dictionary"] = self._peaks_dict
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
