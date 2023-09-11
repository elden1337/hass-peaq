import logging

from homeassistant.core import HomeAssistant
from peaqevcore.common.enums.calltype_enum import CallTypes
from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.servicecalls_dto import ServiceCallsDTO
from peaqevcore.models.chargertype.servicecalls_options import \
    ServiceCallsOptions

from custom_components.peaqev.peaqservice.chargertypes.icharger_type import \
    IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.util.constants import SMARTOUTLET

_LOGGER = logging.getLogger(__name__)


class SmartOutlet(IChargerType):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions, chargertype):
        _LOGGER.warning(
            "You are initiating SmartOutlet as Chargertype. Bare in mind that this chargertype is generic and your results may vary depending on your brand of outlet. If issues emerge, report findings to the developer."
        )
        self._hass = hass
        self._type = chargertype
        self.entities.powerswitch = huboptions.charger.powerswitch
        self.entities.powermeter = huboptions.charger.powermeter
        self.options.charger_is_outlet = True
        self.options.powerswitch_controls_charging = True
        self.chargerstates[ChargeControllerStates.Idle] = ["idle"]
        self.chargerstates[ChargeControllerStates.Connected] = ["connected"]
        self.chargerstates[ChargeControllerStates.Charging] = ["charging"]

    async def async_setup(self) -> bool:
        try:
            await self.async_validate_setup()
            await self.async_set_servicecalls(
                domain=self.domain_name,
                model=ServiceCallsDTO(on=self.call_on, off=self.call_off),
                options=self.servicecalls_options,
            )
            return True
        except Exception:
            _LOGGER.error(f"Could not validate setup for {self.domain_name}.")
        return False

    @property
    def type(self) -> ChargerType:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return SMARTOUTLET

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return ["idle", "connected", "charging"]

    @property
    def call_on(self) -> CallType:
        return CallType(CallTypes.On.value, {})

    @property
    def call_off(self) -> CallType:
        return CallType(CallTypes.Off.value, {})

    @property
    def servicecalls_options(self) -> ServiceCallsOptions:
        return ServiceCallsOptions(
            allowupdatecurrent=False,
            update_current_on_termination=False,
            switch_controls_charger=True,
        )

    async def async_validate_setup(self):
        async def async_check_states(entity: str, type_format: type) -> bool:
            try:
                s = self._hass.states.get(entity)
                if s is not None:
                    if isinstance(s.state, type_format):
                        return True
            except:
                _LOGGER.error(f"Unable to validate outlet-sensor: {entity}")
                return False

        return all(
            [
                await async_check_states(self.entities.powerswitch, str),
                await async_check_states(self.entities.powermeter, float),
            ]
        )
