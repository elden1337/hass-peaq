import logging
from abc import abstractmethod
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
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

CHARGERSTATES_BASE = {
    ChargeControllerStates.Idle: [],
    ChargeControllerStates.Connected: [],
    ChargeControllerStates.Charging: [],
    ChargeControllerStates.Done: [],
}

_LOGGER = logging.getLogger(__name__)

@dataclass
class IChargerType:
    domainname: str = ""
    _hass: HomeAssistant = None
    _max_amps = None
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

    async def async_setup(self) -> bool:
        if self.type is ChargerType.NoCharger:
            return True
        try:
            entities_model = helper.set_entitiesmodel(
                hass=self._hass,
                domain=self.domain_name,
                entity_endings=self.entity_endings,
                entity_schema=self.entities.entityschema,
            )
            if entities_model.valid:
                self.entities.imported_entities = entities_model.imported_entities
                self.entities.entityschema = entities_model.entityschema
        except:
            _LOGGER.debug(f"Could not get a proper entityschema for {self.domain_name}.")
            return False

        try:
            await self.async_set_sensors()
        except Exception:
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
        pass

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
