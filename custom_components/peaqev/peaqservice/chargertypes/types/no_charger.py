import logging

from homeassistant.core import HomeAssistant
from peaqevcore.models.chargertype.servicecalls_dto import ServiceCallsDTO
from peaqevcore.models.chargertype.servicecalls_options import \
    ServiceCallsOptions
from custom_components.peaqev.peaqservice.chargertypes.icharger_type import IChargerType

from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions

_LOGGER = logging.getLogger(__name__)


class NoCharger(IChargerType):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions, chargertype):
        self._type = chargertype

        

    async def async_setup(self):
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

    @property
    def type(self):
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return "No charger"

    @property
    def servicecalls_options(self) -> ServiceCallsOptions:
        return ServiceCallsOptions(
            allowupdatecurrent=False,
            update_current_on_termination=False,
            switch_controls_charger=False,
        )
