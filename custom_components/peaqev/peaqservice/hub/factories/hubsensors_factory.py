from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.hub.hub_sensors import HubSensorsLite, HubSensors, IHubSensors


class HubSensorsFactory:
    @staticmethod
    async def create(options: HubOptions) -> IHubSensors:
        if options.peaqev_lite:
            return HubSensorsLite()
        else:
            return HubSensors()
