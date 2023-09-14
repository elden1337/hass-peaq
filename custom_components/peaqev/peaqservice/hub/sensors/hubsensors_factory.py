from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.peaqev.peaqservice.hub.sensors.ihub_sensors import \
    HubSensors

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub


class HubSensorsFactory:
    @staticmethod
    async def async_create(hub: HomeAssistantHub) -> HubSensors:
        sensors = HubSensors
        return await HubSensorsFactory.async_setup(hub, sensors())

    @staticmethod
    async def async_setup(hub: HomeAssistantHub, sensors: HubSensors) -> HubSensors:
        await sensors.async_setup(
            state_machine=hub.state_machine,
            options=hub.options,
            domain=hub.model.domain,
            chargerobject=hub.chargertype,
        )
        await sensors.async_init_hub_values()
        return sensors
