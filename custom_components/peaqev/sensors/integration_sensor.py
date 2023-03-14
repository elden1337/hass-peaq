
from homeassistant.components.integration.const import METHOD_TRAPEZOIDAL
from homeassistant.components.integration.sensor import (
    IntegrationSensor
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass
)
from homeassistant.const import (
    TIME_HOURS,
    ENERGY_KILO_WATT_HOUR
)

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.util.constants import POWERCONTROLS


class PeaqIntegrationCostSensor(IntegrationSensor):
    device_class = SensorDeviceClass.ENERGY
    def __init__(self, hub, name, entry_id):
        self._entry_id = entry_id
        self.hub = hub
        self._attr_name = f"{self.hub.hubname} {name}"
        self._attr_unique_id = f"{DOMAIN}_{self.hub.hub_id}_{self._attr_name}"
        self._attr_unit_of_measurement = ENERGY_KILO_WATT_HOUR

        super().__init__(
            integration_method=METHOD_TRAPEZOIDAL,
            name=self._attr_name,
            round_digits=5,
            source_entity=f"sensor.{hub.hubname.lower()}_wattage_cost",
            unique_id=self.unique_id,
            unit_prefix="k",
            unit_time=TIME_HOURS
        )

    @property
    def state_class(self):
        """Return state class of unit."""
        return SensorStateClass.TOTAL_INCREASING

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)}}


class PeaqIntegrationSensor(IntegrationSensor):
    device_class = SensorDeviceClass.ENERGY
    def __init__(self, hub, sensor, name, entry_id):
        self._entry_id = entry_id
        self.hub = hub
        self._attr_name = f"{self.hub.hubname} {name}"
        self._attr_unique_id = f"{DOMAIN}_{self.hub.hub_id}_{self._attr_name}"
        self._attr_unit_of_measurement = ENERGY_KILO_WATT_HOUR

        super().__init__(
            integration_method=METHOD_TRAPEZOIDAL,
            name=self._attr_name,
            round_digits=2,
            source_entity=sensor,
            unique_id=self.unique_id,
            unit_prefix="k",
            unit_time=TIME_HOURS
        )

    @property
    def state_class(self):
        """Return state class of unit."""
        return SensorStateClass.TOTAL_INCREASING

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self.hub.hub_id, POWERCONTROLS)}}
