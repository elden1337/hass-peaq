from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from datetime import timedelta

from homeassistant.components.filter.sensor import (TIME_SMA_LAST,
                                                    LowPassFilter,
                                                    OutlierFilter,
                                                    SensorFilter,
                                                    TimeSMAFilter)

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import POWERCONTROLS


async def async_set_filters(hub: HomeAssistantHub, filtertimedelta: timedelta) -> list:
    return [
        LowPassFilter(
            window_size=1,
            precision=0,
            entity=hub.sensors.power.house.entity,
            time_constant=10,
        ),
        TimeSMAFilter(
            window_size=filtertimedelta,
            precision=0,
            entity=hub.sensors.power.house.entity,
            type=TIME_SMA_LAST,
        ),
        OutlierFilter(
            window_size=4,
            precision=0,
            entity=hub.sensors.power.house.entity,
            radius=2,
        ),
    ]


class PeaqAverageSensor(SensorFilter):
    def __init__(self, hub: HomeAssistantHub, entry_id, name, filters):
        self.hub = hub
        self._entry_id = entry_id
        self._attr_name = f"{hub.hubname} {name}"
        super().__init__(
            name=self._attr_name,
            unique_id=self.unique_id,
            entity_id=self.hub.sensors.power.house.entity,
            filters=filters,
        )

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)}}

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"
