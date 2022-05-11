
from homeassistant.const import (
    TIME_HOURS
)
from homeassistant.components.integration.const import METHOD_TRAPEZOIDAL
import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from homeassistant.components.integration.sensor import (
    IntegrationSensor
)
from custom_components.peaqev.const import DOMAIN

class PeaqIntegrationSensor(IntegrationSensor):
    def __init__(self, hub, sensor, name, entry_id):
        self._entry_id = entry_id
        self._hub = hub
        self._attr_name = f"{self._hub.hubname} {name}"
        self._attr_unique_id = f"{DOMAIN}_{self._hub.hub_id}_{self._attr_name}"
        self._unit_of_measurement = "kWh"

        super().__init__(
            integration_method=METHOD_TRAPEZOIDAL,
            name=self._attr_name,
            round_digits=2,
            source_entity=sensor,
            unique_id=self.unique_id,
            unit_prefix="k",
            unit_time=TIME_HOURS
            #unit_of_measurement=self._unit_of_measurement
        )

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._entry_id}_{ex.nametoid(self._attr_name)}"

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}
