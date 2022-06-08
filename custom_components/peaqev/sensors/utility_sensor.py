
from homeassistant.components.utility_meter.sensor import (
    UtilityMeterSensor
)
from peaqevcore.querytypes import HOURLY

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN


class Object():
    pass

METER_OFFSET = Object()
METER_OFFSET.seconds = 0 # pylint:disable=attribute-defined-outside-init
METER_OFFSET.minutes = 0 # pylint:disable=attribute-defined-outside-init
METER_OFFSET.days = 0 # pylint:disable=attribute-defined-outside-init

PERIODS = [HOURLY]


class PeaqUtilitySensor(UtilityMeterSensor):
    def __init__(self, hub, sensor, meter_type, meter_offset, entry_id):
        self._entry_id = entry_id
        self._hub = hub
        self._attr_name = f"{self._hub.hubname} {sensor} {meter_type.lower()}"
        self._unit_of_measurement = "kWh"
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
            unique_id = self.unique_id
        )

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}
