from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.powertools.gainloss.igain_loss import IGainLoss
from custom_components.peaqev.peaqservice.powertools.power_canary.ipower_canary import IPowerCanary
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from custom_components.peaqev.peaqservice.powertools.gainloss.gain_loss import \
    GainLoss
from custom_components.peaqev.peaqservice.powertools.ipower_tools import \
    IPowerTools
from custom_components.peaqev.peaqservice.powertools.power_canary.power_canary import \
    PowerCanary


class PowerTools(IPowerTools):
    def __init__(self, hub: HomeAssistantHub, observer: IObserver, state_machine: IHomeAssistantFacade):
        self._power_canary = PowerCanary(
            fuse_type=hub.options.fuse_type,
            allow_amp_adjustment=hub.chargertype.servicecalls.options.allowupdatecurrent,
            observer=observer,
            peaqev_lite=hub.options.peaqev_lite #todo: decouple from hub
        )
        self._gain_loss = GainLoss(observer=observer, state_machine=state_machine)

    @property
    def power_canary(self) -> IPowerCanary:
        return self._power_canary

    @property
    def gain_loss(self) -> IGainLoss:
        return self._gain_loss


class PowerToolsLite(IPowerTools):

    @property
    def power_canary(self) -> IPowerCanary:
        pass

    @property
    def gain_loss(self) -> IGainLoss:
        pass
