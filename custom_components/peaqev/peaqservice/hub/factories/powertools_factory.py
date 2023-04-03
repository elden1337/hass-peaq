from custom_components.peaqev.peaqservice.powertools.ipower_tools import IPowerTools
from custom_components.peaqev.peaqservice.powertools.power_tools import PowerToolsLite, PowerTools


class PowerToolsFactory:
    @staticmethod
    async def async_create(hub) -> IPowerTools:
        if hub.options.peaqev_lite:
            return PowerToolsLite()
        else:
            return PowerTools(hub)
