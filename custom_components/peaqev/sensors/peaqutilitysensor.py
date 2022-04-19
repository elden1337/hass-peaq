
from homeassistant.components.utility_meter.sensor import (
    UtilityMeterSensor,
    HOURLY
)
from custom_components.peaqev.const import DOMAIN

class Object(object):
    pass

METER_OFFSET = Object()
METER_OFFSET.seconds = 0
METER_OFFSET.minutes = 0
METER_OFFSET.days = 0

PERIODS = [HOURLY]


class PeaqUtilitySensor(UtilityMeterSensor):
    def __init__(self, hub, sensor, meter_type, meter_offset):
        self._hub = hub
        self._attr_name = f"{self._hub.hubname} {sensor} {meter_type.lower()}"
        self._attr_unique_id = f"{DOMAIN}_{self._hub.hub_id}_{self._attr_name}"
        entity = f"sensor.{DOMAIN.lower()}_{sensor}"
        
        super().__init__(
            cron_pattern="{minute} * * * *",
            delta_values=0,
            meter_offset=meter_offset,
            meter_type=meter_type,
            name=self._attr_name,
            net_consumption=True,
            parent_meter=entity,
            source_entity=entity,
            tariff_entity=None,
            tariff=None,
            unique_id = self._attr_unique_id
        )

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}

