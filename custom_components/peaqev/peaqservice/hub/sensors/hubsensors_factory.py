from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.peaqev.peaqservice.chargertypes.icharger_type import IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.models.hub_options import HubOptions
from custom_components.peaqev.peaqservice.hub.sensors.hub_sensors import \
    HubSensors
from custom_components.peaqev.peaqservice.hub.sensors.hub_sensors_base import \
    HubSensorsBase
from custom_components.peaqev.peaqservice.hub.sensors.hub_sensors_lite import \
    HubSensorsLite
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade

if TYPE_CHECKING:
    pass


class HubSensorsFactory:
    @staticmethod
    async def async_create(
            state_machine: IHomeAssistantFacade,
            hub_options: HubOptions,
            domain: str,
            chargerobject: IChargerType
    ) -> HubSensorsBase:
        if hub_options.peaqev_lite:
            sensors = HubSensorsLite
        else:
            sensors = HubSensors
        return await HubSensorsFactory.async_setup(state_machine, hub_options, domain, chargerobject, sensors())

    @staticmethod
    async def async_setup(state_machine: IHomeAssistantFacade,
            hub_options: HubOptions,
            domain: str,
            chargertype: IChargerType, sensors: HubSensors) -> HubSensors:
        await sensors.async_setup(
            state_machine=state_machine,
            options=hub_options,
            domain=domain,
            chargerobject=chargertype,
        )
        if chargertype.type is not ChargerType.NoCharger:
            await sensors.async_set_charger_sensors()
            await sensors.async_init_charger_hub_values()
        await sensors.async_init_hub_values()

        return sensors
