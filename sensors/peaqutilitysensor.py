
from homeassistant.components.utility_meter.sensor import (
    UtilityMeterSensor,
    HOURLY
)
from custom_components.peaq.const import DOMAIN

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
            entity,
            entity,
            self._attr_name,
            meter_type,
            meter_offset,
            0,
            True
        )

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}