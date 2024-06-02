from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from custom_components.peaqev.peaqservice.powertools.ipower_tools import \
    IPowerTools
from custom_components.peaqev.peaqservice.powertools.power_tools import (
    PowerTools, PowerToolsLite)


class PowerToolsFactory:
    @staticmethod
    async def async_create(hub: HomeAssistantHub, observer: IObserver, state_machine: IHomeAssistantFacade) -> IPowerTools:
        if hub.options.peaqev_lite:
            return PowerToolsLite()
        else:
            return PowerTools(hub, observer, state_machine)
