from datetime import timedelta

from homeassistant.components.filter.sensor import (
    OutlierFilter, LowPassFilter,
    TimeSMAFilter, SensorFilter,
    TIME_SMA_LAST
)

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN


class PeaqAverageSensor(SensorFilter):
    def __init__(self, hub, entry_id, name, filtertimedelta):
        self._hub = hub
        self._entry_id = entry_id
        self._attr_name = f"{hub.hubname} {name}"
        super().__init__(
            self._attr_name,
            self.unique_id,
            self._hub.power.house.entity,
            self._set_filters(self._hub, filtertimedelta)
        )

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"

    def _set_filters(self, hub, filtertimedelta:timedelta):
        FILTERS = []

        FILTERS.append(LowPassFilter(1, 0, hub.power.house.entity, 10))
        FILTERS.append(TimeSMAFilter(filtertimedelta, 0, hub.power.house.entity, TIME_SMA_LAST))
        FILTERS.append(OutlierFilter(4, 0, hub.power.house.entity, 2))

        return FILTERS
