from __future__ import annotations

from dataclasses import dataclass

from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.hub.sensors.hub_sensors_base import \
    HubSensorsBase


@dataclass
class HubSensorsLite(HubSensorsBase):
    async def async_setup(self, options: HubOptions, state_machine, domain: str, chargerobject):
        await self.async_setup_base(options, state_machine, domain, chargerobject)
