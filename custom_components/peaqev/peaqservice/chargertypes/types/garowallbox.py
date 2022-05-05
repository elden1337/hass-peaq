from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
from peaqevcore.Models import CHARGERSTATES
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
)
from custom_components.peaqev.peaqservice.chargertypes.calltype import CallType
import logging
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = [] #fix
DOMAINNAME = "garo_wallbox"
UPDATECURRENT = True
#docs: https://github.com/sockless-coding/garo_wallbox/

"""
This is the class that implements a specific chargertype into peaqev.
Note that you need to change:

-manifest.json: add the domain of the charger to after_dependencies
-constants.py: alter the CHARGERTYPES with a new type-constant for your charger. If not, it will not be selectable in config_flow
-chargertypes.py|init: update the clause with your type to return this class as the charger.
"""

"""
states:
'CHANGING'
'SEARCH_COMM'
'INITIALIZATION'
'RCD_FAULT'
'DISABLED'
'OVERHEAT'
'CRITICAL_TEMPERATURE'
'CABLE_FAULT'
'LOCK_FAULT'
'CONTACTOR_FAULT'
'VENT_FAULT'
'DC_ERROR'
'UNKNOWN'
'UNAVAILABLE'
"""

class GaroWallbox(ChargerBase):
    def __init__(self, hass: HomeAssistant, chargerid, auth_required: bool = False):
        super().__init__(hass)
        self._chargerid = chargerid
        self.getentities(DOMAINNAME, ENTITYENDINGS)
        self._chargerstates[CHARGERSTATES.Idle] = ['NOT_CONNECTED']
        self._chargerstates[CHARGERSTATES.Connected] = [
            'CONNECTED',
            'CHARGING_PAUSED',
            'CHARGING_FINISHED',
            'CHARGING_CANCELLED'
        ]
        self._chargerstates[CHARGERSTATES.Charging] = ['CHARGING']
        # self.chargerentity = f"sensor.{self._entityschema}_status"
        # self.powermeter = f"sensor.{self._entityschema}_power"
        # self.powermeter_factor = 1000
        # self.powerswitch = f"switch.{self._entityschema}_is_enabled"
        # self.ampmeter = f"sensor.{self._entityschema}_max_charger_limit"
        # self.ampmeter_is_attribute = False
        self._auth_required = auth_required

        servicecall_params = {
            CHARGER: "entity_id",
            CHARGERID: self._chargerid, #sensor for garo, not id
            CURRENT: "limit"
        }

        _on_call = CallType("set_mode", {"mode": "on", "entity_id": self.chargerentity})
        _off_call = CallType("set_mode", {"mode": "off", "entity_id": self.chargerentity})

        self._set_servicecalls(
            domain=DOMAINNAME,
            on_call=_on_call,
            off_call=_off_call,
            pause_call=None,
            resume_call=None,
            allowupdatecurrent=True,
            update_current_call="set_current_limit",
            update_current_params=servicecall_params
        )
