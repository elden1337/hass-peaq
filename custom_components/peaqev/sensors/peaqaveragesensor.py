from custom_components.peaqev.const import DOMAIN
from datetime import timedelta
from homeassistant.components.filter.sensor import (
    OutlierFilter, LowPassFilter,
    TimeSMAFilter, SensorFilter,
    TIME_SMA_LAST 
    )
import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.util.constants import AVERAGECONSUMPTION

class PeaqAverageSensor(SensorFilter):
    def __init__(self, hub):
        self._hub = hub
        self._attr_name = f"{hub.hubname} {AVERAGECONSUMPTION}"
        self._attr_unique_id = f"{hub.hub_id}_{ex.nametoid(AVERAGECONSUMPTION)}"
        super().__init__(
            self._attr_name,
            self._attr_unique_id,
            self._hub.house_powersensor.entity,
            self._SetFilters(self._hub)
        )

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}

    def _SetFilters(self, hub):
        FILTERS = []

        FILTERS.append(LowPassFilter(1, 0, hub.house_powersensor.entity, 10))
        FILTERS.append(TimeSMAFilter(timedelta(minutes=5), 0, hub.house_powersensor.entity, TIME_SMA_LAST))
        FILTERS.append(OutlierFilter(4, 0, hub.house_powersensor.entity, 2))
        
        return FILTERS

