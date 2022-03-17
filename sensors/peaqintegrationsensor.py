
from homeassistant.const import (
    TIME_HOURS
)

from homeassistant.components.integration.sensor import (
    TRAPEZOIDAL_METHOD,
    IntegrationSensor
)
from custom_components.peaq.const import DOMAIN

class PeaqIntegrationSensor(IntegrationSensor):
    def __init__(self, hub, sensor, name):
        self._hub = hub
        self._attr_name = f"{self._hub.NAME} {name}"
        self._attr_unique_id = f"{DOMAIN}_{self._hub.HUB_ID}_{self._attr_name}"
        
        super().__init__(
            sensor,
            self._attr_name,
            2,
            "k",
            TIME_HOURS,
            None,
            TRAPEZOIDAL_METHOD
        )

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._hub.HUB_ID)}}