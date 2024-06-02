from abc import ABC, abstractmethod

from custom_components.peaqev.peaqservice.hub.models.hub_options import HubOptions
from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade


class IMaxMinController(ABC):
    def __init__(self, options: HubOptions, observer: IObserver, state_machine: IHomeAssistantFacade, max_charge: int, is_active: bool):
        self._max_charge = max_charge
        self.observer = observer
        self.state_machine = state_machine
        self.active: bool = options.price.price_aware
        self.active: bool = is_active
        self.is_on: bool = False
        self._override_max_charge = None
        self._original_total_charge = 0
        self._max_min_limiter: float = 0
        self.override_max_charge: bool = False

    @property
    @abstractmethod
    def max_charge(self) -> int:
        pass

    @property
    @abstractmethod
    def remaining_charge(self) -> float:
        pass

    @property
    @abstractmethod
    def max_min_limiter(self) -> float:
        pass

    @max_min_limiter.setter
    @abstractmethod
    def max_min_limiter(self, val: float):
        pass

    @abstractmethod
    async def async_override_max_charge(self, max_charge: int):
        pass

    @abstractmethod
    async def async_update_maxmin_core(self) -> None:
        pass

    @abstractmethod
    async def async_servicecall_override_charge_amount(self, amount: int):
        pass

    @abstractmethod
    async def async_servicecall_reset_charge_amount(self):
        pass

    @abstractmethod
    async def async_null_max_charge_done(self, val):
        pass

    @abstractmethod
    async def async_null_max_charge(self, val=None):
        pass

    @abstractmethod
    async def async_try_reset_max_charge_sensor(self) -> None:
        pass

    @abstractmethod
    async def async_reset_max_charge_sensor(self) -> None:
        pass

    @abstractmethod
    async def async_update_sensor(self, val):
        pass
