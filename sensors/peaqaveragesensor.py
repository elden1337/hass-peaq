from custom_components.peaq.const import DOMAIN
from datetime import timedelta
from homeassistant.components.filter.sensor import (
    OutlierFilter, LowPassFilter,
    TimeSMAFilter, SensorFilter,
    TIME_SMA_LAST 
    )

class PeaqAverageSensor(SensorFilter):
    def __init__(self, hub):
        self._hub = hub
        self._attr_name = f"{hub.NAME} Average Consumption"
        self._attr_unique_id = f"{hub.HUB_ID}_average_consumption"
        super().__init__(
            self._attr_name,
            self._attr_unique_id,
            self._hub.powersensor.entity,
            self._SetFilters(self._hub)
        )

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.HUB_ID)}}

    def _SetFilters(self, hub):
        FILTERS = []

        FILTERS.append(LowPassFilter(1,0,hub.powersensor.entity,10))
        FILTERS.append(TimeSMAFilter(timedelta(minutes=5), 0, hub.powersensor.entity, TIME_SMA_LAST ))
        FILTERS.append(OutlierFilter(4,0,hub.powersensor.entity,2))
        
        return FILTERS

