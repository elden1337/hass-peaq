import logging

# from homeassistant.core import HomeAssistant
from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.models.chargerstates import CHARGERSTATES
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.servicecalls_dto import ServiceCallsDTO
from peaqevcore.models.chargertype.servicecalls_options import ServiceCallsOptions
from peaqevcore.services.chargertype.chargertype_base import ChargerBase

from custom_components.peaqev.peaqservice.util.constants import (
    ON,
    OFF
)

_LOGGER = logging.getLogger(__name__)

DOMAINNAME = "SmartOutlet"
UPDATECURRENT = False


class SmartOutlet(ChargerBase):
    def __init__(self, hass: HomeAssistant, options: HubOptions):
        self._hass = hass
        self.entities.powerswitch = options.charger.powerswitch
        self.entities.powermeter = options.charger.powermeter
        self.options.powerswitch_controls_charging = True
        self.domainname = DOMAINNAME
        self.chargerstates[CHARGERSTATES.Idle] = []
        self.chargerstates[CHARGERSTATES.Connected] = []
        self.chargerstates[CHARGERSTATES.Charging] = []

        self._set_servicecalls(
            domain=DOMAINNAME,
            model=ServiceCallsDTO(
                on=CallType(ON, {}),
                off=CallType(OFF, {})
            ),
            options=ServiceCallsOptions(
                allowupdatecurrent=UPDATECURRENT,
                update_current_on_termination=False,
                switch_controls_charger = True
            )
        )
