import logging

from peaqevcore.models.chargertype.servicecalls_options import \
    ServiceCallsOptions

from custom_components.peaqev.peaqservice.chargertypes.icharger_type import \
    IChargerType
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade

_LOGGER = logging.getLogger(__name__)


class NoCharger(IChargerType):
    def __init__(self, hass: IHomeAssistantFacade, huboptions: HubOptions, chargertype, observer: IObserver):
        self.observer = observer
        self._type = chargertype

    @property
    def type(self):
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return 'No charger'

    @property
    def servicecalls_options(self) -> ServiceCallsOptions:
        return ServiceCallsOptions(
            allowupdatecurrent=False,
            update_current_on_termination=False,
            switch_controls_charger=False,
        )
