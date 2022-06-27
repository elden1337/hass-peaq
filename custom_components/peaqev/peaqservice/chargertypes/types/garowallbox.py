import logging

from homeassistant.core import HomeAssistant
from peaqevcore.models.chargerstates import CHARGERSTATES

from custom_components.peaqev.peaqservice.chargertypes.calltype import CallType
from custom_components.peaqev.peaqservice.chargertypes.chargerbase import ChargerBase
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
)

_LOGGER = logging.getLogger(__name__)

ENTITYENDINGS = [
    '_current_temperature',
    '_latest_reading_k',
    '_latest_reading',
    '_acc_session_energy',
    '_pilot_level',
    '_current_limit',
    '_nr_of_phases',
    '_current_charging_power',
    '_current_charging_current',
    '_status'
 ]

DOMAINNAME = "garo_wallbox"
UPDATECURRENT = True
#docs: https://github.com/sockless-coding/garo_wallbox/


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
            'CHARGING_CANCELLED'
        ]
        self._chargerstates[CHARGERSTATES.Done] = ['CHARGING_FINISHED']
        self._chargerstates[CHARGERSTATES.Charging] = ['CHARGING']
        self.chargerentity = f"sensor.{self._entityschema}_status"
        self.powermeter = f"sensor.{self._entityschema}_current_charging_power"
        self.powermeter_factor = 1
        # self.powerswitch = f"switch.{self._entityschema}_is_enabled"
        self.ampmeter = f"sensor.{self._entityschema}_current_charging_current"
        self.ampmeter_is_attribute = False
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
            allowupdatecurrent=UPDATECURRENT,
            update_current_call="set_current_limit",
            update_current_params=servicecall_params
        )
