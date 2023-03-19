import logging
from abc import abstractmethod
from dataclasses import dataclass, field

from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.calltype_enum import CallTypes
from peaqevcore.models.chargertype.charger_entities_model import ChargerEntitiesModel
from peaqevcore.models.chargertype.charger_options import ChargerOptions
from peaqevcore.models.chargertype.servicecalls_dto import ServiceCallsDTO
from peaqevcore.models.chargertype.servicecalls_options import ServiceCallsOptions
from peaqevcore.services.chargertype.servicecalls import ServiceCalls

_LOGGER = logging.getLogger(__name__)

CHARGERSTATES_BASE = {
    ChargeControllerStates.Idle:      [],
    ChargeControllerStates.Connected: [],
    ChargeControllerStates.Charging:  [],
    ChargeControllerStates.Done:      []
}


@dataclass
class IChargerType:
    _calls = {}

    domainname: str = ""
    _max_amps = None
    native_chargerstates: list = field(default_factory=lambda: [])
    servicecalls: ServiceCalls = None
    chargerstates = CHARGERSTATES_BASE
    entities = ChargerEntitiesModel
    options = ChargerOptions

    def _set_servicecalls(
            self,
            domain: str,
            model: ServiceCallsDTO,
            options: ServiceCallsOptions,
    ) -> None:
        self.servicecalls = ServiceCalls(domain, model, options)

    @property
    def call_on(self) -> CallType:
        try:
            return self._calls.get(CallTypes.On)
        except:
            _LOGGER.exception(f"Could not fetch call_on for chargertype {self.type}")

    @property
    def call_off(self) -> CallType:
        try:
            return self._calls.get(CallTypes.Off)
        except:
            _LOGGER.exception(f"Could not fetch call_off for chargertype {self.type}")

    @property
    def call_resume(self) -> CallType:
        try:
            return self._calls.get(CallTypes.Resume, self._calls.get(CallTypes.On))
        except:
            _LOGGER.exception(f"Could not fetch call_resume for chargertype {self.type}")

    @property
    def call_pause(self) -> CallType:
        try:
            return self._calls.get(CallTypes.Pause, self._calls.get(CallTypes.Off))
        except:
            _LOGGER.exception(f"Could not fetch call_pause for chargertype {self.type}")

    @property
    def call_update_current(self) -> CallType:
        try:
            return self._calls.get(CallTypes.UpdateCurrent)
        except:
            _LOGGER.exception(f"Could not fetch call_updatecurrent for chargertype {self.type}")

    @property
    def max_amps(self) -> int:
        return self._get_allowed_amps()

    def _get_allowed_amps(self) -> int:
        """update this in your derived type if you have a way of getting max amps"""
        return 16

    #abstracts below

    @property
    @abstractmethod
    def servicecalls_options(self) -> ServiceCallsOptions:
        pass

    @property
    @abstractmethod
    def type(self):
        """type returns the implemented chargertype."""
        pass

    @property
    @abstractmethod
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        pass

    @property
    @abstractmethod
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
        pass

    @property
    @abstractmethod
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        pass


    @abstractmethod
    def validatecharger(self) -> bool:
        pass

    @abstractmethod
    def get_entities(self):
        pass

    @abstractmethod
    def _set_sensors(self, schema):
        pass


