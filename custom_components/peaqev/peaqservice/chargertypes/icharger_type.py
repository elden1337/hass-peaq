import logging
from abc import abstractmethod
from dataclasses import dataclass

from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.charger_entities_model import \
    ChargerEntitiesModel
from peaqevcore.models.chargertype.charger_options import ChargerOptions
from peaqevcore.models.chargertype.servicecalls_dto import ServiceCallsDTO
from peaqevcore.models.chargertype.servicecalls_options import \
    ServiceCallsOptions
from peaqevcore.services.chargertype.servicecalls import ServiceCalls

import custom_components.peaqev.peaqservice.chargertypes.entitieshelper as helper
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade

CHARGERSTATES_BASE = {
    ChargeControllerStates.Idle: [],
    ChargeControllerStates.Connected: [],
    ChargeControllerStates.Charging: [],
    ChargeControllerStates.Done: [],
}

_LOGGER = logging.getLogger(__name__)

@dataclass
class IChargerType:
    domainname: str = ''
    _hass: IHomeAssistantFacade = None
    _max_amps = None
    servicecalls: ServiceCalls = None
    chargerstates = CHARGERSTATES_BASE
    entities = ChargerEntitiesModel
    options = ChargerOptions
    _is_initialized = False
    observer: IObserver = None

    async def async_set_servicecalls(
        self,
        domain: str,
        model: ServiceCallsDTO,
        options: ServiceCallsOptions,
    ) -> bool:
        self.servicecalls = ServiceCalls(domain, model, options)
        return True

    async def async_setup(self) -> bool:
        if self.type is not ChargerType.NoCharger:
            try:
                entitiesobj = helper.set_entitiesmodel(
                    hass=self._hass,
                    domain=self.domain_name,
                    entity_endings=self.entity_endings,
                    entity_schema=self.entities.entityschema,
                )
                if entitiesobj.valid:
                    self.entities.imported_entities = entitiesobj.imported_entities
                    self.entities.entityschema = entitiesobj.entityschema
            except Exception as e:
                _LOGGER.debug(f'Could not get a proper entityschema for {self.domain_name}. Exception: {e}')
                return False

            try:
                await self.async_set_sensors()
            except Exception as e:
                _LOGGER.error(f'Could not set sensors for {self.domain_name}. Exception: {e}')
                return False

        await self.async_set_servicecalls(
            domain=self.domain_name,
            model=ServiceCallsDTO(
                on=self.call_on,
                off=self.call_off,
                pause=self.call_pause,
                resume=self.call_resume,
                update_current=self.call_update_current,
            ),
            options=self.servicecalls_options,
        )

        self.observer.add('charger max amps', self.max_amps)
        self.observer.add('charger type', self.type)
        self.observer.add('charger states', self.native_chargerstates)
        self.observer.add('charger entities', self.entities)
        self.observer.add('charger options', self.options)
        self.observer.add('charger servicecalls', self.servicecalls)

        self.observer.add('charger is initialized', self.is_initialized)
        self.observer.add('charger max amps', self.max_amps)
        self.observer.add('charger domain name', self.domain_name)
        self.observer.add('charger entity endings', self.entity_endings)
        self.observer.add('charger native charger states', self.native_chargerstates)
        self.observer.add('charger on call', self.call_on)
        self.observer.add('charger off call', self.call_off)
        self.observer.add('charger resume call', self.call_resume)
        self.observer.add('charger pause call', self.call_pause)
        self.observer.add('charger update current call', self.call_update_current)
        self.observer.add('charger servicecalls options', self.servicecalls_options)
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
    def type(self) -> ChargerType:
        """type returns the implemented chargertype."""

    @abstractmethod
    async def async_set_sensors(self):
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

    @abstractmethod
    def get_allowed_amps(self) -> int:
        pass

    @abstractmethod
    def validatecharger(self) -> bool: #not used?
        pass

    @abstractmethod
    async def async_get_entities(self): #not used?
        pass
