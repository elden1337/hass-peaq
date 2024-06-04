from abc import abstractmethod, ABC

from custom_components.peaqev.peaqservice.powertools.gainloss.igain_loss import IGainLoss
from custom_components.peaqev.peaqservice.powertools.power_canary.ipower_canary import IPowerCanary


class IPowerTools(ABC):
    @property
    @abstractmethod
    def power_canary(self) -> IPowerCanary:
        pass

    @property
    @abstractmethod
    def gain_loss(self) -> IGainLoss:
        pass
