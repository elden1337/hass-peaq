
from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from peaqevcore.models.locale.enums.time_periods import TimePeriods
import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import POWERCONTROLS
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid


class Object:
    pass

METER_OFFSET = Object()
METER_OFFSET.seconds = 0 # pylint:disable=attribute-defined-outside-init
METER_OFFSET.minutes = 0 # pylint:disable=attribute-defined-outside-init
METER_OFFSET.days = 0 # pylint:disable=attribute-defined-outside-init


class PeaqUtilityCostSensor(UtilityMeterSensor):
    def __init__(self, hub, sensor: any, meter_type: str, meter_offset: str, entry_id: any):
        self._entry_id = entry_id
        self.hub = hub
        self._attr_name = f"{self.hub.hubname} {sensor} {meter_type.lower()}"
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
        #super().start(unit=self._unit_of_measurement)
        #super()._state = 0

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{nametoid(self._attr_name)}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)}}

class PeaqUtilitySensor(UtilityMeterSensor):
    def __init__(self, hub, sensor: any, meter_type: TimePeriods, meter_offset: str, entry_id: any):
        self._entry_id = entry_id
        self.hub = hub
        self._attr_name = f"{self.hub.hubname} {sensor} {meter_type.value.lower()}"
        self._unit_of_measurement = "kWh"
        entity = f"sensor.{DOMAIN.lower()}_{sensor}"

        super().__init__(
            cron_pattern="{minute} * * * *",
            delta_values=0,
            meter_offset=meter_offset,
            meter_type=meter_type.value,
            name=self._attr_name,
            net_consumption=True,
            parent_meter=entity,
            source_entity=entity,
            tariff_entity=None,
            tariff=None,
            unique_id = self.unique_id
        )
        #super().start(unit=self._unit_of_measurement)

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{nametoid(self._attr_name)}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)}}
