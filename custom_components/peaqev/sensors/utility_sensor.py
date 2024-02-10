from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
import inspect
from dataclasses import dataclass

from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from peaqevcore.models.locale.enums.time_periods import TimePeriods

from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid
import logging

_LOGGER = logging.getLogger(__name__)

class Object:
    pass


METER_OFFSET = Object()
METER_OFFSET.seconds = 0  # pylint:disable=attribute-defined-outside-init
METER_OFFSET.minutes = 0  # pylint:disable=attribute-defined-outside-init
METER_OFFSET.days = 0  # pylint:disable=attribute-defined-outside-init


@dataclass(frozen=True)
class UtilityMeterDTO:
    visible_default: bool
    sensor: str
    meter_type: TimePeriods
    entry_id: any


async def async_create_single_utility(hub: HomeAssistantHub, sensor: any, meter_type: TimePeriods, entry_id: any):
    name = f"{hub.hubname} {sensor} {meter_type.value.lower()}"
    source = f"sensor.{DOMAIN.lower()}_{sensor}"
    this_sensor = f"{source}_{meter_type.value.lower()}"
    unique_id = f"{DOMAIN}_{entry_id}_{nametoid(name)}"
    params = {
        "source_entity": source,
        "name": name,
        "meter_type": meter_type.value,
        "meter_offset": METER_OFFSET,
        "net_consumption": True,
        "sensor_always_available": True,
        "tariff": None,
        "tariff_entity": None,
        "periodically_resetting": False,
    }

    signature = inspect.signature(UtilityMeterSensor.__init__)
    if "parent_meter" in signature.parameters:
        params["parent_meter"] = source
    if "delta_values" in signature.parameters:
        params["delta_values"] = False
    if "unique_id" in signature.parameters:
        params["unique_id"] = unique_id
    if "cron_pattern" in signature.parameters:
        params["cron_pattern"] = None

    utility_meter = PeaqUtilitySensor(**params)
    _LOGGER.debug(f"Creating utility meter {name} with entity_id {this_sensor}. Result {utility_meter}")
    utility_meter.entity_id = this_sensor
    return utility_meter


class PeaqUtilitySensor(UtilityMeterSensor):
    @property
    def entity_registry_visible_default(self) -> bool:
        return False

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._attr_unique_id

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state
