from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from peaqevcore.models.locale.enums.time_periods import TimePeriods

from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import POWERCONTROLS
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid


class Object:
    pass


METER_OFFSET = Object()
METER_OFFSET.seconds = 0  # pylint:disable=attribute-defined-outside-init
METER_OFFSET.minutes = 0  # pylint:disable=attribute-defined-outside-init
METER_OFFSET.days = 0  # pylint:disable=attribute-defined-outside-init

from dataclasses import dataclass

DATA_UTILITY = "utility_meter_data"
DATA_TARIFF_SENSORS = "utility_meter_sensors"


@dataclass(frozen=True)
class UtilityMeterDTO:
    visible_default: bool
    sensor: str
    meter_type: TimePeriods
    entry_id: any


class PeaqUtilitySensor(UtilityMeterSensor):
    def __init__(
            self,
            hub,
            hass,
            sensor: any,
            meter_type: TimePeriods,
            entry_id: any,
            visible_default: bool
    ):
        self._entry_id = entry_id
        self.hub = hub
        self._visible_default = visible_default
        self._attr_name = f"{self.hub.hubname} {sensor} {meter_type.value.lower()}"
        self._unit_of_measurement = "kWh"
        self._source = f"sensor.{DOMAIN.lower()}_{sensor}"
        self._parent = f"{self._source}_{meter_type.value.lower()}"

        super().__init__(
            cron_pattern="{minute} * * * *",
            delta_values=0,
            meter_offset=METER_OFFSET,
            meter_type=meter_type.value,
            name=self._attr_name,
            net_consumption=True,
            parent_meter=self._parent,
            source_entity=self._source,
            tariff_entity=None,
            tariff=None,
            unique_id=self.unique_id,
            periodically_resetting=False,
        )
        hass.data[DATA_UTILITY][self._parent] = {DATA_TARIFF_SENSORS: [self]}

    @property
    def entity_registry_visible_default(self) -> bool:
        return self._visible_default

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{nametoid(self._attr_name)}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)}}

# class PeaqUtilityCostSensor(UtilityMeterSensor):
#     def __init__(self, hub, sensor: any, meter_type: str, meter_offset: str, entry_id: any, hass):
#         self._entry_id = entry_id
#         self.hub = hub
#         self._attr_name = f"{self.hub.hubname} {sensor} {meter_type.lower()}"
#         self._unit_of_measurement = "kWh"
#         self._parent = f"sensor.{DOMAIN.lower()}_{sensor}"
#
#         super().__init__(
#             cron_pattern="{minute} * * * *",
#             delta_values=0,
#             meter_offset=meter_offset,
#             meter_type=meter_type,
#             name=self._attr_name,
#             net_consumption=True,
#             parent_meter=self._parent,
#             source_entity=self._parent,
#             tariff_entity=None,
#             tariff=None,
#             unique_id=self.unique_id,
#             periodically_resetting=False,
#         )
#         hass.data[DATA_UTILITY][self._parent] = {DATA_TARIFF_SENSORS: [self]}
#
#     @property
#     def entity_registry_visible_default(self) -> bool:
#         return False
#
#     @property
#     def unique_id(self):
#         """Return a unique ID to use for this sensor."""
#         return f"{DOMAIN}_{self._entry_id}_{nametoid(self._attr_name)}"
#
#     @property
#     def device_info(self):
#         return {"identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)}}


# class PeaqUtilitySensor(UtilityMeterSensor):
#     def __init__(
#         self,
#         hub,
#         sensor: any,
#         meter_type: TimePeriods,
#         meter_offset: str,
#         entry_id: any,
#         hass,
#     ):
#         self._entry_id = entry_id
#         self.hub = hub
#         self._attr_name = f"{self.hub.hubname} {sensor} {meter_type.value.lower()}"
#         self._unit_of_measurement = "kWh"
#         self._parent = f"sensor.{DOMAIN.lower()}_{sensor}"
#
#         super().__init__(
#             cron_pattern="{minute} * * * *",
#             delta_values=0,
#             meter_offset=meter_offset,
#             meter_type=meter_type.value,
#             name=self._attr_name,
#             net_consumption=True,
#             parent_meter=self._parent,
#             source_entity=self._parent,
#             tariff_entity=None,
#             tariff=None,
#             unique_id=self.unique_id,
#             periodically_resetting=False,
#         )
#         hass.data[DATA_UTILITY][self._parent] = {DATA_TARIFF_SENSORS: [self]}
#
#     @property
#     def entity_registry_visible_default(self) -> bool:
#         return False
#
#     @property
#     def unique_id(self):
#         """Return a unique ID to use for this sensor."""
#         return f"{DOMAIN}_{self._entry_id}_{nametoid(self._attr_name)}"
#
#     @property
#     def device_info(self):
#         return {"identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)}}
