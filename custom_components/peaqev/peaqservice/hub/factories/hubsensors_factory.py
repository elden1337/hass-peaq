from custom_components.peaqev.peaqservice.hub.sensors.hub_sensors import HubSensors
from custom_components.peaqev.peaqservice.hub.sensors.hub_sensors_lite import HubSensorsLite
from custom_components.peaqev.peaqservice.hub.sensors.ihub_sensors import IHubSensors


class HubSensorsFactory:
    @staticmethod
    async def async_create(hub) -> IHubSensors:
        sensors = HubSensors
        if hub.options.peaqev_lite:
            sensors = HubSensorsLite
        return await HubSensorsFactory.async_setup(hub, sensors())

    @staticmethod
    async def async_setup(hub, sensors: IHubSensors) -> IHubSensors:
        await sensors.async_setup(
            state_machine=hub.state_machine,
            options=hub.options,
            domain=hub.domain,
            chargerobject=hub.chargertype)
        await sensors.async_init_hub_values()
        return sensors
