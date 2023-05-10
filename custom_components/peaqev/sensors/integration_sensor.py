from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.peaqev.sensors.sensorbase import SensorBase

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

from homeassistant.components.integration.const import (  # pylint: disable=import-error
    METHOD_LEFT,
    METHOD_TRAPEZOIDAL,
)
from homeassistant.components.integration.sensor import (
    IntegrationSensor,
)  # pylint: disable=import-error
from homeassistant.components.sensor import (
    SensorDeviceClass,
)  # pylint: disable=import-error
from homeassistant.const import (  # pylint: disable=import-error
    ENERGY_KILO_WATT_HOUR,
    UnitOfTime,
)

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import POWERCONTROLS


class PeaqIntegrationCostSensor(IntegrationSensor):
    def __init__(self, hub: HomeAssistantHub, name, entry_id):
        self._entry_id = entry_id
        self.hub = hub
        self._attr_name = f"{self.hub.hubname} {name}"
        self._attr_unit_of_measurement = ENERGY_KILO_WATT_HOUR

        super().__init__(
            integration_method=METHOD_TRAPEZOIDAL,
            name=self._attr_name,
            round_digits=5,
            source_entity=f"sensor.{hub.hubname.lower()}_wattage_cost",
            unique_id=self.unique_id,
            unit_prefix="k",
            unit_time=UnitOfTime.HOURS,
        )

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SensorDeviceClass.ENERGY

    @property
    def name(self):
        return self._attr_name

    @property
    def entity_registry_visible_default(self) -> bool:
        return False

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)}}


class PeaqIntegrationSensor(IntegrationSensor):
    def __init__(self, hub, sensor, name, entry_id):
        self._entry_id = entry_id
        self.hub = hub
        self._attr_name = f"{self.hub.hubname} {name}"
        self._attr_unit_of_measurement = ENERGY_KILO_WATT_HOUR

        super().__init__(
            integration_method=METHOD_TRAPEZOIDAL,
            name=self._attr_name,
            round_digits=2,
            source_entity=sensor,
            unique_id=self.unique_id,
            unit_prefix="k",
            unit_time=UnitOfTime.HOURS,
        )

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SensorDeviceClass.ENERGY

    @property
    def name(self):
        return self._attr_name

    @property
    def entity_registry_visible_default(self) -> bool:
        return False

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)}}
