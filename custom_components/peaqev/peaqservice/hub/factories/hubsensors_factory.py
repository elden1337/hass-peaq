from custom_components.peaqev.peaqservice.hub.models.hub_options import HubOptions
from custom_components.peaqev.peaqservice.hub.sensors.hub_sensors import HubSensors
from custom_components.peaqev.peaqservice.hub.sensors.hub_sensors_lite import HubSensorsLite
from custom_components.peaqev.peaqservice.hub.sensors.ihub_sensors import IHubSensors


class HubSensorsFactory:
    @staticmethod
    async def async_create(options: HubOptions) -> IHubSensors:
        if options.peaqev_lite:
            return HubSensorsLite()
        else:
            return HubSensors()
