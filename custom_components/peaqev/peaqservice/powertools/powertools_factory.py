from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from custom_components.peaqev.peaqservice.powertools.ipower_tools import \
    IPowerTools
from custom_components.peaqev.peaqservice.powertools.power_tools import (
    PowerTools, PowerToolsLite)


class PowerToolsFactory:
    @staticmethod
    async def async_create(hub: HomeAssistantHub) -> IPowerTools:
        if hub.options.peaqev_lite:
            return PowerToolsLite()
        else:
            return PowerTools(hub)
