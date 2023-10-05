from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.hub.sensors.ihub_sensors import \
    HubSensors, HubSensorsLite

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub


class HubSensorsFactory:
    @staticmethod
    async def async_create(hub: HomeAssistantHub) -> HubSensors:
        if hub.options.peaqev_lite:
            sensors = HubSensorsLite
        else:
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
        if hub.chargertype.type is not ChargerType.NoCharger:
            await sensors.async_set_charger_sensors()
            await sensors.async_init_charger_hub_values()
        await sensors.async_init_hub_values()

        return sensors
