from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from custom_components.peaqev.peaqservice.powertools.gainloss.gain_loss import \
    GainLoss
from custom_components.peaqev.peaqservice.powertools.ipower_tools import \
    IPowerTools
from custom_components.peaqev.peaqservice.powertools.power_canary.power_canary import \
    PowerCanary


class PowerTools(IPowerTools):
    def __init__(self, hub: HomeAssistantHub):
        self._hub = hub
        self._power_canary = PowerCanary(hub=hub)
        self._gain_loss = GainLoss(hub=hub)

    @property
    def power_canary(self) -> PowerCanary:
        return self._power_canary

    @property
    def gain_loss(self) -> GainLoss:
        return self._gain_loss


class PowerToolsLite(IPowerTools):
    pass
