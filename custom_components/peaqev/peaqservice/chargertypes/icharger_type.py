from abc import abstractmethod
from dataclasses import dataclass, field

from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.charger_entities_model import ChargerEntitiesModel
from peaqevcore.models.chargertype.charger_options import ChargerOptions
from peaqevcore.models.chargertype.servicecalls_dto import ServiceCallsDTO
from peaqevcore.models.chargertype.servicecalls_options import ServiceCallsOptions
from peaqevcore.services.chargertype.servicecalls import ServiceCalls

CHARGERSTATES_BASE = {
    ChargeControllerStates.Idle: [],
    ChargeControllerStates.Connected: [],
    ChargeControllerStates.Charging: [],
    ChargeControllerStates.Done: [],
}


@dataclass
class IChargerType:
    domainname: str = ""
    _max_amps = None
    native_chargerstates: list = field(default_factory=lambda: [])  # type: ignore
    servicecalls: ServiceCalls = None
    chargerstates = CHARGERSTATES_BASE
    entities = ChargerEntitiesModel
    options = ChargerOptions
    _is_initialized = False

    async def async_set_servicecalls(
        self,
        domain: str,
        model: ServiceCallsDTO,
        options: ServiceCallsOptions,
    ) -> bool:
        self.servicecalls = ServiceCalls(domain, model, options)
        return True

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    @is_initialized.setter
    def is_initialized(self, val: bool) -> None:
        self._is_initialized = val

    @property
    def max_amps(self) -> int:
        if self._max_amps is None:
            return 16
        return self._max_amps

    @max_amps.setter
    def max_amps(self, val) -> None:
        self._max_amps = val

    @property
    @abstractmethod
    def type(self):
        """type returns the implemented chargertype."""

    @abstractmethod
    def get_allowed_amps(self) -> int:
        pass

    @abstractmethod
    def validatecharger(self) -> bool:
        pass

    @abstractmethod
    async def async_get_entities(self):
        pass

    @abstractmethod
    async def async_set_sensors(self):
        pass

    @abstractmethod
    async def async_setup(self) -> bool:
        pass

    @property
    @abstractmethod
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""

    @property
    @abstractmethod
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""

    @property
    @abstractmethod
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""

    @property
    @abstractmethod
    def call_on(self) -> CallType:
        pass

    @property
    @abstractmethod
    def call_off(self) -> CallType:
        pass

    @property
    @abstractmethod
    def call_resume(self) -> CallType:
        pass

    @property
    @abstractmethod
    def call_pause(self) -> CallType:
        pass

    @property
    @abstractmethod
    def call_update_current(self) -> CallType:
        pass

    @property
    @abstractmethod
    def servicecalls_options(self) -> ServiceCallsOptions:
        pass
