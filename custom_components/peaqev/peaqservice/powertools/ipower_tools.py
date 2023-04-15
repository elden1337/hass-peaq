from abc import abstractmethod

from custom_components.peaqev.peaqservice.powertools.gainloss.gain_loss import \
    GainLoss
from custom_components.peaqev.peaqservice.powertools.power_canary.power_canary import \
    PowerCanary


class IPowerTools:
    @property
    @abstractmethod
    def power_canary(self) -> PowerCanary:
        pass

    @property
    @abstractmethod
    def gain_loss(self) -> GainLoss:
        pass
